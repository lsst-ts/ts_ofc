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
from lsst.ts.ofc import OFCData, SensitivityMatrix, StateEstimator


class TestStateEstimator(unittest.TestCase):
    """Test the OptStateEsti class."""

    def setUp(self):
        self.ofc_data = OFCData("lsst")

        self.estimator = StateEstimator(self.ofc_data, rcond=1e-5)

        self.wfe = np.loadtxt(
            pathlib.Path(__file__).parent.absolute()
            / "testData"
            / "lsst_wfs_error_iter0.z4c"
        )

        dofs = np.loadtxt(
            pathlib.Path(__file__).parent.absolute() / "testData" / "lsst_dof_iter0.txt"
        )
        self.dofs = dofs[:, 1]

        # Constuct the double zernike sensitivity matrix
        self.dz_sensitivity_matrix = SensitivityMatrix(self.ofc_data)

        self.sensor_name_list = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]

        self.field_angles = [
            self.ofc_data.sample_points[sensor] for sensor in self.sensor_name_list
        ]

    def mean_squared_residual(self, new_array, reference_array):
        return np.sum((new_array - reference_array) ** 2) / np.sum(reference_array**2)

    def compute_sensitivity_matrix(self, field_angles, rotation_angle):
        # Evaluate sensitivity matrix at sensor positions
        sensitivity_matrix = self.dz_sensitivity_matrix.evaluate(
            field_angles, rotation_angle
        )

        # Select sensitivity matrix only at used zernikes
        sensitivity_matrix = sensitivity_matrix[
            :, self.dz_sensitivity_matrix.ofc_data.zn3_idx, :
        ]

        # Reshape sensitivity matrix to dimensions
        # (#zk * #sensors, # dofs) = (19 * #sensors, 50)
        size = sensitivity_matrix.shape[2]
        sensitivity_matrix = sensitivity_matrix.reshape((-1, size))

        # Select sensitivity matrix only at used degrees of freedom
        sensitivity_matrix = sensitivity_matrix[
            ..., self.dz_sensitivity_matrix.ofc_data.dof_idx
        ]

        return sensitivity_matrix

    def test_dof_state(self):
        # Compute sensitivity matrix
        sensitivity_matrix = self.compute_sensitivity_matrix(
            self.field_angles, rotation_angle=0.0
        )

        # Compute optical state estimate
        state = self.estimator.dof_state(
            "R", self.wfe, self.sensor_name_list, rotation_angle=0.0
        )

        # Check number of degrees of freedom matches the specified
        n_values = len(self.estimator.ofc_data.dof_idx)
        self.assertEqual(len(state), n_values)

        # Check derived wavefront from state estimate
        # matches the one from original dofs
        residual = self.mean_squared_residual(
            sensitivity_matrix @ self.dofs, sensitivity_matrix @ state
        )
        assert residual < 1e-3

    def test_dof_state_trim_zn_dof(self):
        # Set zernike indices to Z4-Z9
        self.estimator.ofc_data.zn3_idx = np.arange(5)
        self.dz_sensitivity_matrix.ofc_data.zn3_idx = np.arange(5)

        # Compute sensitivity matrix
        sensitivity_matrix = self.compute_sensitivity_matrix(
            self.field_angles, rotation_angle=0.0
        )

        # Set used Degrees of Freedom
        new_comp_dof_idx = dict(
            m2HexPos=np.ones(5, dtype=bool),
            camHexPos=np.ones(5, dtype=bool),
            M1M3Bend=np.zeros(20, dtype=bool),
            M2Bend=np.zeros(20, dtype=bool),
        )
        self.estimator.ofc_data.comp_dof_idx = new_comp_dof_idx

        # Compute optical state estimate
        state = self.estimator.dof_state(
            "R", self.wfe, self.sensor_name_list, rotation_angle=0.0
        )

        # Check number of degrees of freedom matches the specified
        n_values = len(self.estimator.ofc_data.dof_idx)
        self.assertEqual(len(state), n_values)

        # Check derived wavefront from state estimate matches
        # the one from original dofs
        residual = self.mean_squared_residual(
            sensitivity_matrix @ self.dofs, sensitivity_matrix[..., :n_values] @ state
        )
        assert residual < 1e-2

    def test_dof_state_not_enough_zk(self):
        # Set zernike indices to Z4-Z8
        self.estimator.ofc_data.zn3_idx = np.arange(4)

        # Set used Degrees of Freedom
        new_comp_dof_idx = dict(
            m2HexPos=np.ones(5, dtype=bool),
            camHexPos=np.ones(5, dtype=bool),
            M1M3Bend=np.zeros(20, dtype=bool),
            M2Bend=np.zeros(20, dtype=bool),
        )
        new_comp_dof_idx["M1M3Bend"][:10] = True
        self.estimator.ofc_data.comp_dof_idx = new_comp_dof_idx

        # Check that optical state estimation raises error
        # when # dofs > # zernikes
        with self.assertRaises(RuntimeError):
            self.estimator.dof_state(
                "R", self.wfe, self.sensor_name_list, rotation_angle=0.0
            )


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
