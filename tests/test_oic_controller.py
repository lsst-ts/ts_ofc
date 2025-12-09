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

from lsst.ts.ofc import OFCData, OICController


class TestOICController(unittest.TestCase):
    """Test the OICController class."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.ofc_data = OFCData("lsst")

        # Set small motion penalty to allow for larger corrections
        self.ofc_data.motion_penalty = 0.00001
        self.controller = OICController(self.ofc_data)

        test_dof_state0 = np.zeros(50)
        test_dof_state0[15] = 0.5
        test_dof_state0[25] = 1.5
        test_dof_state0[45] = 1.5

        self.controller.dof_state0 = test_dof_state0
        self.controller.reset_dof_state()

        self.filter_name = "R"

    def test_uk_nogain_x0(self) -> None:
        """Test the uk method with x0 reference."""
        self.ofc_data.xref = "x0"

        sum_uk = np.zeros(50)
        for _ in range(5):
            uk = self.controller.uk(
                self.filter_name,
                self.controller.dof_state0 - sum_uk,
            )
            sum_uk += uk

        # Check length of correction vector matches used number of DOFs
        self.assertEqual(len(uk), len(self.ofc_data.dof_idx))

        # Check that corrections match original dof_state after three
        # iterations. Note that other degrees of freedom values are
        # not checked because degenerate solutions exist.
        assert self.mean_squared_residual(sum_uk[15], 0.5) < 5e-2
        assert self.mean_squared_residual(sum_uk[25], 1.5) < 5e-2
        assert self.mean_squared_residual(sum_uk[45], 1.5) < 5e-2

    def test_set_aggregated_state(self) -> None:
        """Test the set_aggregated_state method."""
        new_state = np.ones(50)

        self.controller.set_aggregated_state(new_state)

        # Check that the aggregated state is the same as the new state
        np.testing.assert_array_almost_equal(
            self.controller.aggregated_state,
            new_state,
            decimal=5,
            err_msg="Aggregated state does not match new state.",
        )

    def mean_squared_residual(self, new_array: np.ndarray, reference_array: np.ndarray) -> float:
        """Compute the mean squared residual between two arrays.

        Parameters
        ----------
        new_array : np.ndarray
            New array.
        reference_array : np.ndarray
            Reference array.

        Returns
        -------
        float
            Mean squared residual.
        """
        return np.sum((new_array - reference_array) ** 2) / np.sum(reference_array**2)

    def test_uk_nogain_0(self) -> None:
        """Test the uk method with 0 reference."""
        self.ofc_data.xref = "0"
        uk = self.controller.uk(self.filter_name, self.controller.dof_state0)

        # Check length of correction vector matches used number of DOFs
        self.assertEqual(len(uk), len(self.ofc_data.dof_idx))

        # Check for ref "0" our corrections is minus the initial DOF state
        assert self.mean_squared_residual(uk, self.controller.dof_state0) < 1e-6

    def test_uk_nogain_x00(self) -> None:
        """Test the uk method with x00 reference."""
        self.ofc_data.xref = "x00"
        uk = self.controller.uk(self.filter_name, self.controller.dof_state0)

        # Check length of correction vector matches used number of DOFs
        self.assertEqual(len(uk), len(self.ofc_data.dof_idx))

        # Check for ref "x00" our corrections match the corrections
        # for x0, when dof_state = dof_state0
        self.ofc_data.xref = "x0"
        uk_ref0 = self.controller.uk(self.filter_name, self.controller.dof_state0)

        assert self.mean_squared_residual(uk_ref0, uk) < 1e-6

    def test_all_xref_ok(self) -> None:
        """Test all xref methods are available."""
        for xref in self.ofc_data.xref_list:
            self.assertTrue(hasattr(self.controller, f"calc_uk_{xref}"))

    def test_gain(self) -> None:
        """Test the gain property."""
        for gain in {0.0, 0.25, 0.5, 0.75, 1.0}:
            with self.subTest(gain=gain):
                self.controller.kp = gain
                self.assertEqual(self.controller.kp, gain)

    def test_set_pssn_gain_unconfigured(self) -> None:
        """Test setting the PSSN gain without FWHM data."""
        with self.assertRaises(RuntimeError):
            self.controller.set_pssn_gain()

    def test_set_pssn_gain(self) -> None:
        """Test setting the PSSN gain."""
        fwhm_values = np.ones((4, 19)) * 0.2
        sensor_names = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]

        self.controller.set_fwhm_data(fwhm_values, sensor_names)

        self.controller.set_pssn_gain()

        self.assertTrue(self.controller.kp, self.controller.default_gain)

        fwhm_values = np.ones((4, 19))

        self.controller.set_fwhm_data(fwhm_values, sensor_names)

        self.controller.set_pssn_gain()

        self.assertTrue(self.controller.kp, 1.0)

    def test_pssn_data(self) -> None:
        """Test the pssn_data property."""
        self.assertTrue("sensor_names" in self.controller.pssn_data)
        self.assertTrue("pssn" in self.controller.pssn_data)
        self.assertTrue(self.controller.pssn_data["sensor_names"] == [])
        self.assertTrue(self.controller.pssn_data["pssn"] == [])


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
