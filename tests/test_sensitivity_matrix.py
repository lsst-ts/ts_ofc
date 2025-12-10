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
from glob import glob
from pathlib import Path

import numpy as np
import yaml

from lsst.ts.ofc import OFCData, SensitivityMatrix


class TestSensitivityMatrix(unittest.TestCase):
    """Test the SensitivityMatrix class."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.ofc_data = OFCData("lsst")

        self.sensitivity_matrix = SensitivityMatrix(self.ofc_data)

        # Define the field angles for the 31 Gaussian Quadrature points
        self.field_angles = [
            self.ofc_data.gq_points[sensor] for sensor in range(len(self.ofc_data.gq_points))
        ]
        self.unrotated_sensitivity_matrix = -self.sensitivity_matrix.evaluate(field_angles=self.field_angles)

        self.unrotated_sensitivity_matrix[..., [0, 1, 3, 5, 6, 8] + list(range(30, 50))] *= -1

        gq_sensitivity_matrix_file = Path(
            glob(
                str(
                    Path(__file__).parent.absolute()
                    / "testData"
                    / "legacy"
                    / f"lsst_{self.ofc_data.sen_m_filename_root}*.yaml"
                )
            )[0]
        )

        with open(gq_sensitivity_matrix_file, "r") as fp:
            self.gq_sensitivity_matrix = np.array(yaml.safe_load(fp))

            # Note that we use only up to 31 index for the old
            # sensitivity matrix, because the last 4 elements
            # corresponded to the corner wavvefront sensors
            # which we have excluded from the unrotated_sensitivity_matrix.
            self.gq_sensitivity_matrix = self.gq_sensitivity_matrix[:31, ...]

            # Because the old sensitivity matrix was in the Zemax Coordinate
            # System we need to swap the following zernikes:
            swap = np.array([5, 8, 10, 13, 15, 16, 18, 20])
            self.gq_sensitivity_matrix[:, swap - self.ofc_data.znmin] *= -1

            # Similarly, we need to swap the following gaussian
            # quadrature points because the old sensitivity matrix
            # was in the Zemax Coordinate System and therefore
            # there is a flip in the x direction. So the following
            # swap, flips those GQ points that have opposite x sign.
            swap_gq = [
                0,
                4,
                3,
                2,
                1,
                6,
                5,
                10,
                9,
                8,
                7,
                12,
                11,
                16,
                15,
                14,
                13,
                18,
                17,
                22,
                21,
                20,
                19,
                24,
                23,
                28,
                27,
                26,
                25,
                30,
                29,
            ]
            self.gq_sensitivity_matrix = self.gq_sensitivity_matrix[swap_gq, :]

            # Change the units of the tilts to degrees
            self.gq_sensitivity_matrix[:, :, [3, 4, 8, 9]] *= 3600

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

    def test_dz_sensitivity_matrix(self) -> None:
        """Test the dz sensitivity matrix with legacy values."""
        # Check that the sensitivity matrix for dz is the same as the one
        # that we had before the last ts_ofc refactor and before the bending
        # modes were updated.
        # This means that we will check that the sensitivity matrix is the same
        # Only for the hexapod degrees of freedom which were not changed.
        for dof in np.arange(10):
            assert (
                self.mean_squared_residual(
                    self.unrotated_sensitivity_matrix[..., : self.gq_sensitivity_matrix.shape[1], dof],
                    self.gq_sensitivity_matrix[..., dof],
                )
                < 2e-4
            )

    def test_rotation(self) -> None:
        """Test the rotation of the sensitivity matrix."""
        angles = [20, 60, 45, 90, 180, 270]

        # Define  degrees of freedom that excite zernikes across the field
        # uniformly (radial order 0). In particular, we look at those that are
        # constant accross the field. For these any rotation
        # should give the same result.
        dof_zks_r0 = [
            (0, 4),  # M2 dz excites focus Z4 uniformly across the field
            (1, 8),  # M2 dx excites coma Z8 uniformly across the field
            (4, 8),  # M2 dRY excites coma Z8 uniformly across the field
            (7, 7),  # Camera dy excites coma Z7 uniformly across the field
            (10, 5),  # M1M3 B1 excites astigmatism Z5 uniformly across the field
            (12, 4),  # M1M3 B3 excites focus Z4 uniformly across the field
            (18, 14),  # M1M3 B9 excites quadrafoil Z14 uniformly across the field
            (26, 18),  # M1M3 B17 excites 2nd trefoil Z18 uniformly across the field
            (32, 10),  # M2 B3 excites trefoil Z10 uniformly across the field
            (37, 14),  # M2 B8 excites quadrafoil Z14 uniformly across the field
            (42, 20),  # M2 B13 excites pentafoil Z20 uniformly across the field
            (47, 11),  # M2 B18 excites primary spherical Z11 uniformly across the field
        ]

        # Define degrees of freedom that excite zernikes across the field
        # with radial order r = 2 (they are symmetric when rotate 180 degrees,
        # but not when rotated 90 degrees or any other angle)
        dof_zks_r2 = [
            (15, 7),  # M1M3 B6 excites come Z7 w/ r=2 across the field
            (21, 5),  # M1M3 B12 excites astigmatism Z5 w/ r=2 across the field
            (24, 7),  # M1M3 B15 excites come Z7 w/ r=2 across the field
            (25, 19),  # M1M3 B16 excites 2nd trefoil Z19 w/ r=2 across the field
            (29, 12),  # M1M3 B20 excites 2nd astigmatism Z12 w/ r=2 across the field
        ]

        for angle in angles:
            rotated_sensitivity_matrix = -self.sensitivity_matrix.evaluate(
                field_angles=self.field_angles, rotation_angle=angle
            )
            rotated_sensitivity_matrix[..., [0, 1, 3, 5, 6, 8] + list(range(30, 50))] *= -1

            # Check for zernikes excited uniformally
            # accross the field (radial order 0)
            # Need to subtract 4, because the sensitivity matrix goes from
            # Z4 to Z22, where Z4 corresponds to index 0.
            for dof, zernike in dof_zks_r0:
                residual = self.mean_squared_residual(
                    rotated_sensitivity_matrix[:, zernike - 4, dof],
                    self.unrotated_sensitivity_matrix[:, zernike - 4, dof],
                )
                assert residual < 1e-3

            # Check for excited zernikes that are symmetric
            # when rotate 180 degrees, but not when rotated 90
            # degrees or any other angle.
            for dof, zernike in dof_zks_r2:
                residual = self.mean_squared_residual(
                    rotated_sensitivity_matrix[:, zernike - 4, dof],
                    self.unrotated_sensitivity_matrix[:, zernike - 4, dof],
                )

                assert (residual < 1e-3) if angle == 180 else (residual > 1e-3)


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
