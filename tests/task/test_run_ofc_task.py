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

import unittest

import numpy as np
from astropy.table import Table

import lsst.pipe.base as pipeBase
from lsst.afw.cameraGeom import DetectorType
from lsst.obs.lsst import LsstCam
from lsst.ts.ofc.task.run_ofc_task import RunOfcTask, RunOfcTaskConfig


class TestRunOfcTask(unittest.TestCase):
    """Test the RunOfcTask class."""

    def makeTestZernikeTable(
        self,
        detector_type: str | None = None,
        noll_indices: list[int] | None = None,
        band: str = "r",
        rot_angle: float = 0.0,
    ) -> Table:
        """Create a minimal aggregateZernikesAvg-style table for testing.

        Parameters
        ----------
        detector_type : str, optional
            Type of detector to use. Can be "wavefront" or "science".
            Defaults to "wavefront".
        noll_indices : list of int, optional
            Noll indices for Zernike coefficients. Defaults to [4..21].
        band : str
            Filter band name to store in table metadata.
        rot_angle : float
            Rotation angle (degrees) to store in table metadata.

        Returns
        -------
        table : `astropy.table.Table`

        Raises
        ------
        ValueError
            If an invalid detector_type is provided.
        """
        if noll_indices is None:
            noll_indices = np.arange(4, 23)  # 18 Zernikes

        n_zk = len(noll_indices)
        camera = LsstCam.getCamera()

        if detector_type in ["wavefront", None]:
            detector_names = [det.getName() for det in camera if det.getType() == DetectorType.WAVEFRONT]
        elif detector_type == "science":
            detector_names = [det.getName() for det in camera if det.getType() == DetectorType.SCIENCE]
        else:
            raise ValueError(f"Invalid detector_type: {detector_type}")

        rng = np.random.default_rng(42)
        zk_data = rng.normal(scale=50e-9, size=(len(detector_names), n_zk))  # ~50 nm RMS, in meters

        table = Table(
            {
                "detector": detector_names,
                "zk_deviation_CCS": zk_data,
            }
        )
        table.meta["nollIndices"] = noll_indices
        table.meta["band"] = band
        table.meta["rotAngle"] = rot_angle

        return table

    def testValidateConfig(self) -> None:
        """
        Test that the RunOfcTaskConfig variables appear in the task correctly.
        """
        config = RunOfcTaskConfig()
        task = RunOfcTask(config=config)
        # Test default values
        self.assertEqual(task.dof_indices, tuple(range(50)))
        self.assertFalse(task.subtract_intrinsics)
        self.assertEqual(task.column_name, "zk_deviation_CCS")

        # Test custom values
        dof_indices = [0, 1, 2, 3, 4, 5, 31]
        config.dofIndices = dof_indices
        config.subtractIntrinsics = True
        config.tableColumnName = "zk_deviation"
        task = RunOfcTask(config=config)
        self.assertEqual(task.dof_indices, dof_indices)
        self.assertTrue(task.subtract_intrinsics)
        self.assertEqual(task.column_name, "zk_deviation")

    def testRunOfcTask(self) -> None:
        """Test the RunOfcTask class."""
        config = RunOfcTaskConfig()
        config.dofIndices = [0, 1, 2, 3, 4, 5, 31]
        task = RunOfcTask(config=config)

        zern_table = self.makeTestZernikeTable()
        task_out = task.run(zern_table, LsstCam.getCamera())
        # Test that the output is a Struct with the expected attributes
        self.assertIsInstance(task_out, pipeBase.Struct)
        self.assertIsInstance(task_out.ofcCorrections, np.ndarray)
        self.assertEqual(len(task_out.ofcCorrections), 50)

    def testRunOFC(self) -> None:
        """Test the _runOfc method of RunOfcTask."""
        config = RunOfcTaskConfig()
        config.dofIndices = [0, 1, 2, 3, 4, 5, 31]
        task = RunOfcTask(config=config)

        zern_table = self.makeTestZernikeTable()
        ofc_corrections = task._runOfc(zern_table, LsstCam.getCamera())
        # Test that the output is an array of the expected shape and values
        self.assertIsInstance(ofc_corrections, np.ndarray)
        self.assertEqual(len(ofc_corrections), 50)
        # Test that the corrections for the specified DOF indices
        # are non-zero and the rest are zero
        zero_vals = np.isin(np.arange(50), config.dofIndices, invert=True)
        np.testing.assert_array_equal(ofc_corrections[zero_vals], np.zeros(50 - len(config.dofIndices)))
        self.assertTrue(np.all(ofc_corrections[config.dofIndices]))
