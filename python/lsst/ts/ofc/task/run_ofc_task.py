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

from typing import Any, Optional

import numpy as np
from astropy.table import Table

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
from lsst.afw.cameraGeom import Camera
from lsst.fgcmcal.utilities import lookupStaticCalibrations
from lsst.pipe.base import connectionTypes as ct
from lsst.ts.ofc import OFC, OFCData
from lsst.ts.ofc.utils import get_config_dir, get_dof_names
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
        storageClass="ArrowAstropy",
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
    ofc_calc: Optional[OFC]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # Set instance variables from config
        self.dof_indices = self.config.dofIndices
        self.column_name = self.config.tableColumnName
        self.subtract_intrinsics = self.config.subtractIntrinsics

        # Useful if running interactively to have access
        # to the OFC object after the task has run
        self.ofc_calc = None

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
            A struct containing:
                - ofcCorrections : `numpy.ndarray`
                  Corrections for the individual componets.
                  Order is: M2 Hexapod, Camera Hexapod,
                  M1M3 and M2.
        """

        if camera.getName() == "LSSTCam":
            ofc_data = OFCData("lsst")
        else:
            raise ValueError(f"Unsupported camera {camera.getName()}")

        self.ofc_calc = OFC(ofc_data)
        noll_indices = aggregateZernikesAvg.meta["nollIndices"]
        j_max = max(noll_indices)
        j_min = min(noll_indices)
        self.ofc_calc.ofc_data.zn_selected = noll_indices

        used_dofs = np.isin(np.arange(50), self.dof_indices)
        self.log.info(f"Using DOF indices: {np.where(used_dofs)[0]}")
        dof_name_file = get_config_dir() / "state0_in_dof.yaml"
        self.log.info(f"DOF Names: {get_dof_names(dof_name_file, self.dof_indices)}")

        self.ofc_calc.ofc_data.comp_dof_idx = {
            "m2HexPos": np.array([val for val in used_dofs[:5]], dtype=bool),
            "camHexPos": np.array([val for val in used_dofs[5:10]], dtype=bool),
            "M1M3Bend": np.array([val for val in used_dofs[10:30]], dtype=bool),
            "M2Bend": np.array([val for val in used_dofs[30:]], dtype=bool),
        }
        self.ofc_calc.controller.reset_history()

        # If we require ts_wep as a prerequisite for functionality
        # in the future, we can replace this with makeDense from ts_wep.utils.
        # But for now we avoid the dependency on ts_wep with this.
        wfe_list = list()
        for wfe in aggregateZernikesAvg[self.column_name]:
            zern_out = np.zeros(j_max - j_min + 1)
            for i, noll in enumerate(noll_indices):
                zern_out[noll - j_min] = wfe[i]
            wfe_list.append(zern_out)

        self.ofc_calc.calculate_corrections(
            np.array(wfe_list),
            sensor_ids=[camera[det].getId() for det in aggregateZernikesAvg["detector"]],
            filter_name=aggregateZernikesAvg.meta["band"],
            rotation_angle=aggregateZernikesAvg.meta["rotAngle"],
            subtract_intrinsics=self.subtract_intrinsics,
        )
        aggregated_state = self.ofc_calc.controller.aggregated_state

        return pipeBase.Struct(ofcCorrections=aggregated_state)
