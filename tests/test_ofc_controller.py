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

from lsst.ts.ofc import OFCController, OFCData, StateEstimator


class TestOFCController(unittest.TestCase):
    """Test the OFCController class."""

    def setUp(self):
        self.ofc_data = OFCData("lsst")

        estimator = StateEstimator(self.ofc_data)

        wfe = np.loadtxt(
            pathlib.Path(__file__).parent.absolute()
            / "testData"
            / "lsst_wfs_error_iter0.z4c"
        )

        sensor_name_list = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]

        field_idx = [
            estimator.ofc_data.field_idx[sensor_name]
            for sensor_name in sensor_name_list
        ]

        self.filter_name = "r"
        self.state = estimator.dof_state(self.filter_name, wfe, field_idx, rotation_angle = 0.0)

        self.ofc_controller = OFCController(self.ofc_data)

        test_dof_state0 = np.ones(len(self.ofc_controller.dof_state0))
        self.ofc_controller.dof_state0 = test_dof_state0
        self.ofc_controller.reset_dof_state()

    def test_uk_nogain_x0(self):
        self.ofc_data.xref = "x0"

        uk = self.ofc_controller.uk(self.filter_name, self.state)
        print(self.state)

        print(uk)

        self.assertEqual(len(uk), len(self.ofc_data.dof_idx))
        self.assertAlmostEqual(uk[0], -9.44847541, places=7)
        self.assertAlmostEqual(uk[1], -2.53792714, places=7)
        self.assertAlmostEqual(uk[2], -0.53851520, places=7)

    def test_uk_nogain_0(self):
        self.ofc_data.xref = "0"
        uk = self.ofc_controller.uk(self.filter_name, self.state)

        self.assertEqual(len(uk), len(self.ofc_data.dof_idx))
        self.assertAlmostEqual(uk[0], -113.62056585, places=7)
        self.assertAlmostEqual(uk[1], -89.94878290, places=7)
        self.assertAlmostEqual(uk[2], 30.05926538, places=7)

    def test_uk_nogain_x00(self):
        self.ofc_data.xref = "x00"
        uk = self.ofc_controller.uk(self.filter_name, self.state)

        self.assertEqual(len(uk), len(self.ofc_data.dof_idx))
        self.assertAlmostEqual(uk[0], -9.44847541, places=7)
        self.assertAlmostEqual(uk[1], -2.53792714, places=7)
        self.assertAlmostEqual(uk[2], -0.53851520, places=7)

    def test_all_xref_ok(self):
        for xref in self.ofc_data.xref_list:
            self.assertTrue(hasattr(self.ofc_controller, f"calc_uk_{xref}"))

    def test_bad_gain(self):
        with self.assertRaises(ValueError):
            self.ofc_controller.gain = -0.5

        with self.assertRaises(ValueError):
            self.ofc_controller.gain = 1.5

    def test_gain(self):
        for gain in {0.0, 0.25, 0.5, 0.75, 1.0}:
            with self.subTest(gain=gain):
                self.ofc_controller.gain = gain
                self.assertEqual(self.ofc_controller.gain, gain)


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
