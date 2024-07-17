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
from lsst.ts.ofc import OFCData, PIDController


class TestPIDController(unittest.TestCase):
    """Test the PIDController class."""

    def setUp(self):
        self.ofc_data = OFCData("lsst")
        self.ofc_data.controller_filename = "pid_controller.yaml"
        self.pid_controller = PIDController(self.ofc_data)
        self.pid_controller.kp = 1.0
        self.pid_controller.ki = 0.1
        self.pid_controller.kd = 0.05
        self.pid_controller.setpoint = np.ones(50)
        self.pid_controller.previous_error = np.zeros(50)
        self.pid_controller.integral = np.zeros(50)

        self.filter_name = "R"
        self.dof_state = np.ones(50)
        self.dof_state[:10] = 0.5

    def test_control_step_response(self):
        """Test control outputs based on a simple input and PID settings."""
        expected_uk = self.calculate_expected_uk(self.dof_state)

        uk = self.pid_controller.control_step(self.filter_name, self.dof_state)

        np.testing.assert_array_almost_equal(
            uk,
            expected_uk,
            decimal=5,
            err_msg="PID control output does not match expected values.",
        )

    def calculate_expected_uk(self, dof_state):
        """Calculate expected control output for given DOF state."""
        integral = self.pid_controller.integral.copy()
        error = self.pid_controller.setpoint - dof_state
        integral += error
        derivative = error - self.pid_controller.previous_error
        uk = (
            self.pid_controller.kp * error
            + self.pid_controller.ki * integral
            + self.pid_controller.kd * derivative
        )

        return uk

    def test_subset_of_dofs(self):
        """Test control output for a subset of DOFs."""
        new_comp_dof_idx = dict(
            m2HexPos=np.zeros(5, dtype=bool),
            camHexPos=np.ones(5, dtype=bool),
            M1M3Bend=np.zeros(20, dtype=bool),
            M2Bend=np.zeros(20, dtype=bool),
        )

        self.pid_controller.ofc_data.comp_dof_idx = new_comp_dof_idx
        self.pid_controller.reset_history()

        initial_state = 0.7 * np.ones(5)
        uk = self.pid_controller.control_step(self.filter_name, initial_state)

        self.assertEqual(len(uk), 5)

    def test_reset_history(self):
        """Test resetting the history of the controller."""
        uk = self.pid_controller.control_step(self.filter_name, self.dof_state)
        self.pid_controller.aggregate_state(uk, self.ofc_data.dof_idx)
        self.pid_controller.control_step(self.filter_name, self.dof_state)

        final_integral = self.pid_controller.integral.copy()
        final_previous_error = self.pid_controller.previous_error.copy()

        self.pid_controller.reset_history()

        if id(self.pid_controller.dof_state0) == id(self.pid_controller.dof_state):
            raise AssertionError("Initial DOF state not reset correctly.")

        if np.array_equal(
            self.pid_controller.integral,
            final_integral,
        ):
            raise AssertionError("Integral history not reset correctly.")

        if np.array_equal(
            self.pid_controller.previous_error,
            final_previous_error,
        ):
            raise AssertionError("Previous error not reset correctly.")

        np.testing.assert_array_equal(
            self.pid_controller.integral,
            self.pid_controller.setpoint[self.pid_controller.ofc_data.dof_idx]
            - self.pid_controller.dof_state[self.pid_controller.ofc_data.dof_idx],
        )
        np.testing.assert_array_equal(
            self.pid_controller.previous_error,
            self.pid_controller.setpoint[self.pid_controller.ofc_data.dof_idx]
            - self.pid_controller.dof_state[self.pid_controller.ofc_data.dof_idx],
        )

    def test_derivative_filter(self):
        """Test derivative filter."""
        self.pid_controller.derivative_filter_coeff = 0.5
        initial_state = 0.7 * np.ones(50)
        self.pid_controller.control_step(self.filter_name, initial_state)
        previous_derivative = self.pid_controller.filtered_derivative.copy()

        # Change in error should reflect in derivative term
        new_state = 0.8 * np.ones(50)
        self.pid_controller.control_step(self.filter_name, new_state)

        expected_derivative = 0.5 * (
            (self.pid_controller.setpoint - new_state) - previous_derivative
        )
        np.testing.assert_array_equal(
            self.pid_controller.filtered_derivative,
            expected_derivative,
            "Derivative calculation does not match expected.",
        )

    def test_integral_behavior(self):
        """Test integral behavior over multiple steps."""
        initial_state = 0.7 * np.ones(50)
        self.pid_controller.control_step(self.filter_name, initial_state)
        self.pid_controller.control_step(self.filter_name, initial_state)
        # Check if integral is accumulating correctly
        np.testing.assert_array_equal(
            self.pid_controller.integral.squeeze(),
            2 * (self.pid_controller.setpoint - initial_state),
            "Integral not accumulating correctly.",
        )

    def test_derivative_behavior(self):
        """Test derivative impact on control step."""
        initial_state = 0.7 * np.ones(50)
        self.pid_controller.control_step(self.filter_name, initial_state)

        # Change in error should reflect in derivative term
        new_state = 0.8 * np.ones(50)
        self.pid_controller.control_step(self.filter_name, new_state)

        expected_derivative = (self.pid_controller.setpoint - new_state) - (
            self.pid_controller.setpoint - initial_state
        )
        np.testing.assert_array_equal(
            self.pid_controller.previous_error
            - (self.pid_controller.setpoint - initial_state),
            expected_derivative,
            "Derivative calculation does not match expected.",
        )


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
