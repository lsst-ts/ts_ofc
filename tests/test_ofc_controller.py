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
from lsst.ts.ofc import OFCController, OFCData


class TestOFCController(unittest.TestCase):
    """Test the OFCController class."""

    def setUp(self):
        self.ofc_data = OFCData("lsst")
        # Set small motion penalty to allow for larger corrections
        self.ofc_data.motion_penalty = 0.0001
        self.ofc_controller = OFCController(self.ofc_data)

        test_dof_state0 = np.zeros(50)
        test_dof_state0[15] = 0.5
        test_dof_state0[25] = 1.5
        test_dof_state0[45] = 1.5

        self.ofc_controller.dof_state0 = test_dof_state0
        self.ofc_controller.reset_dof_state()

        self.filter_name = "r"

    def test_uk_nogain_x0(self):
        self.ofc_data.xref = "x0"

        sum_uk = np.zeros(50)
        for _ in range(3):
            uk = self.ofc_controller.uk(
                self.filter_name, self.ofc_controller.dof_state0 + sum_uk
            )
            sum_uk += uk

        # Check length of correction vector matches used number of DOFs
        self.assertEqual(len(uk), len(self.ofc_data.dof_idx))

        # Check that corrections match original dof_state after three
        # iterations. Note that other degrees of freedom values are
        # not checked because degenerate solutions exist.
        assert self.mean_squared_residual(-sum_uk[15], 0.5) < 5e-2
        assert self.mean_squared_residual(-sum_uk[25], 1.5) < 5e-2
        assert self.mean_squared_residual(-sum_uk[45], 1.5) < 5e-2

    def mean_squared_residual(self, new_array, reference_array):
        return np.sum((new_array - reference_array) ** 2) / np.sum(reference_array**2)

    def test_uk_nogain_0(self):
        self.ofc_data.xref = "0"
        uk = self.ofc_controller.uk(self.filter_name, self.ofc_controller.dof_state0)

        # Check length of correction vector matches used number of DOFs
        self.assertEqual(len(uk), len(self.ofc_data.dof_idx))

        # Check for ref "0" our corrections is minus the initial DOF state
        assert self.mean_squared_residual(-uk, self.ofc_controller.dof_state0) < 1e-6

    def test_uk_nogain_x00(self):
        self.ofc_data.xref = "x00"
        uk = self.ofc_controller.uk(self.filter_name, self.ofc_controller.dof_state0)

        # Check length of correction vector matches used number of DOFs
        self.assertEqual(len(uk), len(self.ofc_data.dof_idx))

        # Check for ref "x00" our corrections match the corrections
        # for x0, when dof_state = dof_state0
        self.ofc_data.xref = "x0"
        uk_ref0 = self.ofc_controller.uk(
            self.filter_name, self.ofc_controller.dof_state0
        )

        assert self.mean_squared_residual(uk_ref0, uk) < 1e-6

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
