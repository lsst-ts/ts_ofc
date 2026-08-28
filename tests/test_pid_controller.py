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

    def setUp(self) -> None:
        """Set up the test case."""
        self.ofc_data = OFCData("lsst")
        self.ofc_data.controller_filename = "pid_controller.yaml"
        self.pid_controller = PIDController(self.ofc_data)
        self.pid_controller.kp = 1.0
        self.pid_controller.ki = 0.1
        self.pid_controller.kd = 0.05
        self.pid_controller.setpoint = np.ones(50)
        self.pid_controller.integral = np.zeros(50)

        self.filter_name = "R"
        self.dof_state = np.ones(50)
        self.dof_state[:10] = 0.5

    def test_control_step_response(self) -> None:
        """Test control outputs based on a simple input and PID settings."""
        expected_uk = self.calculate_expected_uk(self.dof_state)

        uk = self.pid_controller.control_step(self.filter_name, self.dof_state)

        np.testing.assert_array_almost_equal(
            uk,
            expected_uk,
            decimal=5,
            err_msg="PID control output does not match expected values.",
        )

    def calculate_expected_uk(self, dof_state: np.ndarray) -> np.ndarray:
        """Calculate expected control output for given DOF state.

        Parameters
        ----------
        dof_state : np.ndarray
            DOF state.

        Returns
        -------
        np.ndarray
            Expected control output.
        """
        integral = self.pid_controller.integral.copy()
        error = self.pid_controller.setpoint - dof_state
        if self.pid_controller.use_leaky_integrator:
            previous_error = list(self.pid_controller.previous_error) + [error]
            maxlen = self.pid_controller.previous_error.maxlen
            assert maxlen is not None
            previous_error = previous_error[-maxlen:]
            integral = np.sum(
                self.pid_controller.integral_weights[-len(previous_error) :] * np.array(previous_error),
                axis=0,
            )
        else:
            integral += error
        previous_error = (
            self.pid_controller.previous_error[-1]
            if len(self.pid_controller.previous_error) > 0
            else np.zeros(len(self.pid_controller.ofc_data.dof_idx))
        )
        derivative = error - previous_error
        uk = (
            self.pid_controller.kp * error
            + self.pid_controller.ki * integral
            + self.pid_controller.kd * derivative
        )

        return uk

    def test_subset_of_dofs(self) -> None:
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

    def test_reset_history(self) -> None:
        """Test resetting the history of the controller."""
        uk = self.pid_controller.control_step(self.filter_name, self.dof_state)
        self.pid_controller.aggregate_state(uk, self.ofc_data.dof_idx)
        self.pid_controller.control_step(self.filter_name, self.dof_state)

        final_integral = self.pid_controller.integral.copy()

        self.pid_controller.reset_history()

        if id(self.pid_controller.dof_state0) == id(self.pid_controller.dof_state):
            raise AssertionError("Initial DOF state not reset correctly.")

        if np.array_equal(
            self.pid_controller.integral,
            final_integral,
        ):
            raise AssertionError("Integral history not reset correctly.")

        np.testing.assert_array_equal(
            self.pid_controller.integral,
            np.zeros(len(self.pid_controller.ofc_data.dof_idx)),
        )
        self.assertEqual(len(self.pid_controller.previous_error), 0)

    def test_derivative_filter(self) -> None:
        """Test derivative filter."""
        self.pid_controller.derivative_filter_coeff = 0.5
        initial_state = 0.7 * np.ones(50)
        self.pid_controller.control_step(self.filter_name, initial_state)
        previous_derivative = self.pid_controller.filtered_derivative.copy()

        # Change in error should reflect in derivative term
        new_state = 0.8 * np.ones(50)
        self.pid_controller.control_step(self.filter_name, new_state)

        expected_derivative = 0.5 * ((self.pid_controller.setpoint - new_state) - previous_derivative)
        np.testing.assert_array_equal(
            self.pid_controller.filtered_derivative,
            expected_derivative,
            "Derivative calculation does not match expected.",
        )

    def test_proportional_gain_array(self) -> None:
        """Test setting proportional gain as an array."""
        kp_array = np.linspace(0.5, 1.5, len(self.pid_controller.ofc_data.dof_idx))
        self.pid_controller.kp = kp_array
        self.pid_controller.ki = 0.0
        self.pid_controller.kd = 0.0

        initial_state = 0.7 * np.ones(50)
        uk = self.pid_controller.control_step(self.filter_name, initial_state)

        expected_uk = kp_array * (self.pid_controller.setpoint - initial_state)
        np.testing.assert_array_almost_equal(
            uk,
            expected_uk,
            decimal=5,
            err_msg="PID control output with gain array does not match expected values.",
        )

    def test_cumulative_integral_behavior(self) -> None:
        """Test cumulative integral behavior over multiple steps."""
        self.pid_controller.use_leaky_integrator = False
        initial_state = 0.7 * np.ones(50)
        self.pid_controller.control_step(self.filter_name, initial_state)
        self.pid_controller.control_step(self.filter_name, initial_state)
        # Check if integral is accumulating correctly
        np.testing.assert_array_equal(
            self.pid_controller.integral.squeeze(),
            2 * (self.pid_controller.setpoint - initial_state),
            "Integral not accumulating correctly.",
        )

    def test_leaky_integral_behavior(self) -> None:
        """Test leaky integral behavior over multiple steps."""
        self.pid_controller.use_leaky_integrator = True
        initial_state = 0.7 * np.ones(50)
        error = self.pid_controller.setpoint - initial_state

        self.pid_controller.control_step(self.filter_name, initial_state)
        np.testing.assert_array_equal(
            self.pid_controller.integral.squeeze(),
            error,
            "Leaky integral should include the current error.",
        )

        self.pid_controller.control_step(self.filter_name, initial_state)
        np.testing.assert_array_almost_equal(
            self.pid_controller.integral.squeeze(),
            (1 + self.ofc_data.i_factor) * error,
            err_msg="Leaky integral should include current and previous errors.",
        )

        self.pid_controller.control_step(self.filter_name, initial_state)
        np.testing.assert_array_almost_equal(
            self.pid_controller.integral.squeeze(),
            (1 + self.ofc_data.i_factor + self.ofc_data.i_factor**2) * error,
            err_msg="Leaky integral should weight older errors by i_factor.",
        )

    def test_derivative_behavior(self) -> None:
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
            self.pid_controller.previous_error[-1] - (self.pid_controller.setpoint - initial_state),
            expected_derivative,
            "Derivative calculation does not match expected.",
        )


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
