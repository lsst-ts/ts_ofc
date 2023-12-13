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

__all__ = ["SensitivityMatrix"]

import galsim
import numpy as np

from .ofc_data import OFCData


class SensitivityMatrix:
    """Class to handle the sensitivity matrix.

    Parameters
    ----------
    ofc_data : `lsst.ts.ofc.ofc_data.OFCData`
        OFC data.
    """

    def __init__(self, ofc_data: OFCData) -> None:
        self.ofc_data = ofc_data

    def evaluate(
        self,
        field_angles: list,
        rotation_angle: float = 0.0,
    ) -> np.ndarray:
        """Evaluate the sensitivity matrix for a given rotation angle.

        Parameters
        ----------
        rotation_angle : `float`
            Rotation angle in degrees.
        field_angles : `list` [`tuple` [`float`, `float`]]
            List of tuples field angles in degrees.
            [(field_x, field_y)]

        Returns
        -------
        rotated_sensitivity_matrix : numpy.ndarray [float]
            Sensitivity matrix for the given rotation angle in degree.
        """

        # Get the field angles
        field_x, field_y = zip(*field_angles)

        # Convert rotation angle to radians
        rotation_angle = np.deg2rad(rotation_angle)

        # If using double zernikes, compute the sensitivity matrix
        # using galsim DoubleZernikes
        rotated_sensitivity_matrix = np.array(
            [
                np.array(
                    [
                        zk.coef
                        for zk in galsim.zernike.DoubleZernike(
                            self.ofc_data.sensitivity_matrix[..., dof_idx],
                            # Rubin annuli
                            uv_inner=self.ofc_data.config["pupil"]["radius_inner"],
                            uv_outer=self.ofc_data.config["pupil"]["radius_outer"],
                            xy_inner=self.ofc_data.config["obscuration"][
                                "radius_inner"
                            ],
                            xy_outer=self.ofc_data.config["obscuration"][
                                "radius_outer"
                            ],
                        ).rotate(theta_uv=rotation_angle)(field_x, field_y)
                    ]
                )
                for dof_idx in np.arange(self.ofc_data.sensitivity_matrix.shape[2])
            ]
        )

        # Reshape the sensitivity matrix to be
        # (#field_points, #zernikes, #dofs)
        rotated_sensitivity_matrix = np.einsum("ijk->jki", rotated_sensitivity_matrix)

        # Subselect the relevant zernike coefficients
        # to include in the sensitivity matrix.
        rotated_sensitivity_matrix = rotated_sensitivity_matrix[
            :, self.ofc_data.znmin : self.ofc_data.znmax + 1, :
        ]

        return rotated_sensitivity_matrix
