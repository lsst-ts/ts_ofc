# This file is part of ts_ofc.
#
# Developed for Vera Rubin Observatory.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["RunOfcTaskConnections", "RunOfcTaskConfig", "RunOfcTask"]

from typing import Any

import numpy as np
from astropy.table import Table

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
from lsst.afw.cameraGeom import Camera
from lsst.fgcmcal.utilities import lookupStaticCalibrations
from lsst.pipe.base import connectionTypes as ct
from lsst.ts.ofc import OFC, OFCData
from lsst.utils.timer import timeMethod


class RunOfcTaskConnections(
    pipeBase.PipelineTaskConnections,
    dimensions=["instrument", "visit"],  # type: ignore
):
    aggregateZernikesAvg = ct.Input(
        doc="Visit-level table of donuts and Zernikes",
        dimensions=("visit", "instrument"),
        storageClass="AstropyTable",
        name="aggregateZernikesAvg",
        multiple=True,
    )
    camera = ct.PrerequisiteInput(
        name="camera",
        storageClass="Camera",
        doc="Input camera to construct complete exposures.",
        dimensions=["instrument"],
        isCalibration=True,
        lookupFunction=lookupStaticCalibrations,
    )
    ofcCorrections = ct.Output(
        doc="Visit-level table of OFC corrections",
        dimensions=("visit", "instrument"),
        storageClass="AstropyTable",
        name="ofcCorrections",
    )


class RunOfcTaskConfig(
    pipeBase.PipelineTaskConfig,
    pipelineConnections=RunOfcTaskConnections,  # type: ignore
):
    dofIndices: pexConfig.Field = pexConfig.ListField(
        dtype=int,
        doc="List of indices of up to 50 degrees of freedom to use for OFC.",
        default=tuple(range(50)),
    )
    subtractIntrinsics: pexConfig.Field = pexConfig.Field(
        dtype=bool,
        doc="Whether to subtract the intrinsic Zernike coefficients"
        + " from the input table before running OFC.",
        default=False,
    )
    tableColumnName: pexConfig.Field = pexConfig.Field(
        dtype=str,
        doc="Name of the column in the input table that contains the Zernike " + "coefficients.",
        default="zk_deviation_CCS",
    )


class RunOfcTask(pipeBase.PipelineTask):
    """PipelineTask to run OFC on a visit-level table of Zernikes."""

    ConfigClass = RunOfcTaskConfig
    _DefaultName = "runOfcTask"
    config: RunOfcTaskConfig

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.dof_indices = self.config.dofIndices
        self.column_name = self.config.tableColumnName
        self.subtract_intrinsics = self.config.subtractIntrinsics

    @timeMethod
    def run(self, aggregateZernikesAvg: Table, camera: Camera) -> pipeBase.Struct:
        """Run OFC on a visit-level table of donuts and Zernikes.

        Parameters
        ----------
        aggregateZernikesAvg : `lsst.afw.table.Table`
            Visit-level table of donuts and Zernikes.
        camera : `lsst.afw.cameraGeom.Camera`
            Camera object.

        Returns
        -------
        `lsst.pipe.base.Struct`
            A struct containing the visit-level table of OFC corrections.
        """

        ofcCorrections = self._runOfc(aggregateZernikesAvg, camera)

        return pipeBase.Struct(ofcCorrections=ofcCorrections)

    def _runOfc(self, aggregateZernikesAvg: Table, camera: Camera) -> np.ndarray:
        """Run OFC on a visit-level table of donuts and Zernikes. This is a
        separate method so that it can be easily tested.

        Parameters
        ----------
        aggregateZernikesAvg : `lsst.afw.table.Table`
            Visit-level table of donuts and Zernikes.
        camera : `lsst.afw.cameraGeom.Camera`
            Camera object.

        Returns
        -------
        ofcCorrections : `numpy.ndarray`
            Corrections for the individual componets. Order is: M2 Hexapod,
            Camera Hexapod, M1M3 and M2.
        """

        if camera.getName() == "LSSTCam":
            ofc_data = OFCData("lsst")
        else:
            raise ValueError(f"Unsupported camera {camera.getName()}")

        ofc_calc = OFC(ofc_data)
        noll_indices = aggregateZernikesAvg.meta["nollIndices"]
        j_max = max(noll_indices)
        j_min = min(noll_indices)
        ofc_calc.ofc_data.zn_selected = noll_indices

        use_dofs = np.isin(np.arange(50), self.dof_indices)
        self.log.info(f"Using DOF indices: {np.where(use_dofs)[0]}")

        ofc_calc.ofc_data.comp_dof_idx = {
            "m2HexPos": np.array([val for val in use_dofs[:5]], dtype=bool),
            "camHexPos": np.array([val for val in use_dofs[5:10]], dtype=bool),
            "M1M3Bend": np.array([val for val in use_dofs[10:30]], dtype=bool),
            "M2Bend": np.array([val for val in use_dofs[30:]], dtype=bool),
        }
        ofc_calc.controller.reset_history()

        self.ofc_calc = ofc_calc

        wfe_list = list()
        for wfe in aggregateZernikesAvg[self.column_name]:
            zern_out = np.zeros(j_max - j_min + 1)
            for i, noll in enumerate(noll_indices):
                zern_out[noll - j_min] = wfe[i]
            wfe_list.append(zern_out)

        ofc_calc.calculate_corrections(
            np.array(wfe_list),
            sensor_ids=[camera[det].getId() for det in aggregateZernikesAvg["detector"]],
            filter_name=aggregateZernikesAvg.meta["band"],
            rotation_angle=aggregateZernikesAvg.meta["rotAngle"],
            subtract_intrinsics=self.subtract_intrinsics,
        )
        aggregated_state = ofc_calc.controller.aggregated_state

        return aggregated_state
