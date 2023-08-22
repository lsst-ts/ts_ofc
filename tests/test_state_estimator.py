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

import pathlib
import unittest

import numpy as np

from lsst.ts.ofc import OFCData, StateEstimator


class TestStateEstimator(unittest.TestCase):
    """Test the OptStateEsti class."""

    def setUp(self):
        self.ofc_data = OFCData("lsst")

        self.estimator = StateEstimator(self.ofc_data)

        self.wfe = np.loadtxt(
            pathlib.Path(__file__).parent.absolute()
            / "testData"
            / "lsst_wfs_error_iter0.z4c"
        )

        sensor_name_list = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]

        self.field_idx = [
            self.estimator.ofc_data.field_idx[sensor_name]
            for sensor_name in sensor_name_list
        ]

    def test_dof_state(self):
        state = self.estimator.dof_state(
            "r", self.wfe, self.field_idx, rotation_angle=0.0
        )

        n_values = len(self.estimator.ofc_data.dof_idx)

        self.assertEqual(len(state), n_values)
        self.assertAlmostEqual(state[3], -1.14304491e-03, places=4)
        self.assertAlmostEqual(state[12], -2.85609953e-03, places=4)
        self.assertAlmostEqual(state[46], 6.42305288e-03, places=4)

    def test_dof_state_trim_zn_dof(self):
        self.estimator.ofc_data.zn3_idx = np.arange(5)
        new_comp_dof_idx = dict(
            m2HexPos=np.ones(5, dtype=bool),
            camHexPos=np.ones(5, dtype=bool),
            M1M3Bend=np.zeros(20, dtype=bool),
            M2Bend=np.zeros(20, dtype=bool),
        )
        self.estimator.ofc_data.comp_dof_idx = new_comp_dof_idx

        state = self.estimator.dof_state(
            "r", self.wfe, self.field_idx, rotation_angle=0.0
        )
        print(state)

        n_values = len(self.estimator.ofc_data.dof_idx)

        self.assertEqual(len(state), n_values)
        self.assertAlmostEqual(state[0], -278.90163287)
        self.assertAlmostEqual(state[1], 327.86599287)
        self.assertAlmostEqual(state[2], 654.60883647)

    def test_dof_state_not_enough_zk(self):
        self.estimator.ofc_data.zn3_idx = np.arange(4)

        new_comp_dof_idx = dict(
            m2HexPos=np.ones(5, dtype=bool),
            camHexPos=np.ones(5, dtype=bool),
            M1M3Bend=np.zeros(20, dtype=bool),
            M2Bend=np.zeros(20, dtype=bool),
        )
        new_comp_dof_idx["M1M3Bend"][:10] = True

        self.estimator.ofc_data.comp_dof_idx = new_comp_dof_idx

        with self.assertRaises(RuntimeError):
            self.estimator.dof_state("r", self.wfe, self.field_idx, rotation_angle=0.0)


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
