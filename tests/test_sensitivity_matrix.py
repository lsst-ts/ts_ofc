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

    def setUp(self):
        self.ofc_data = OFCData("lsst")

        self.sensitivity_matrix = SensitivityMatrix(self.ofc_data)

        self.field_angles = [self.ofc_data.gq_points[sensor] for sensor in range(31)]
        self.unrotated_sensitivity_matrix = self.sensitivity_matrix.evaluate(
            field_angles=self.field_angles
        )

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

    def mean_squared_residual(self, new_array, reference_array):
        return np.sum((new_array - reference_array) ** 2) / np.sum(reference_array**2)

    def test_dz_sensitivity_matrix(self):
        print(self.ofc_data.gq_points)
        # Check that the sensitivity matrix for dz is the same as the one
        # that we had before the last ts_ofc refactor.
        for dof in np.arange(50):
            print(dof)
            print(
                self.mean_squared_residual(
                    self.unrotated_sensitivity_matrix[..., dof],
                    self.gq_sensitivity_matrix[..., dof],
                )
            )
            assert (
                self.mean_squared_residual(
                    self.unrotated_sensitivity_matrix[..., dof],
                    self.gq_sensitivity_matrix[..., dof],
                )
                < 2e-3
            )

    def test_rotation(self):
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
            rotated_sensitivity_matrix = self.sensitivity_matrix.evaluate(
                field_angles=self.field_angles, rotation_angle=angle
            )

            # Check for zernikes excited uniformally
            # accross the field (radial order 0)
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
