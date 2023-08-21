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

import numpy as np
import numpy.typing as npt
from typing import Tuple, List
import galsim
from .utils import get_field_angle

class SensitivityMatrix:
    """Class to handle the sensitivity matrix.

    Parameters
    ----------
    ofc_data : `lsst.ts.ofc.ofc_data.OFCData`
        OFC data.
    """

    def __init__(self, ofc_data, sensor_names: None | list = None) -> None:
        self.ofc_data = ofc_data

        self.sensor_names = sensor_names

    def evaluate(
        self, rotation_angle: float, 
    ) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """Evaluate the sensitivity matrix for a given rotation angle.

        Parameters
        ----------
        rotation_angle : `float`
            Rotation angle in degrees.
        sensor_names : list [str] or None, optional
            List of sensor names. If None, uses all the Gaussian 
            Quadrature points are used.

        Returns
        -------
        rotated_sensitivity_matrix : numpy.ndarray [float]
            Sensitivity matrix for the given rotation angle in degree.
        field_idx : numpy.ndarray [ float ]
            Field indices for the sensors.
        """

        # Convert rotation angle to radians
        rotation_angle = np.deg2rad(rotation_angle)

        # If sensor_names is None get sensitivity matrix at all GQ points
        if self.sensor_names is None:
            # Create array for all the GQ points
            field_idx = np.arange(self.ofc_data.gq_field_angles.shape[0])
            # Retrieve field angles for each GQ point from ofc_data
            field_x, field_y = zip(*self.ofc_data.gq_field_angles)

        else:
            # Obtain the field indices for the sensors
            field_idx = np.array(
                [self.ofc_data.field_idx[sensor_name] for sensor_name in self.sensor_names]
            )
            # Get the field angles for the sensors
            field_x, field_y = get_field_angle(self.sensor_names)

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
                            uv_inner=self.ofc_data.config.pupil.R_inner,
                            uv_outer=self.ofc_data.config.pupil.R_outer,
                            xy_inner=self.ofc_data.config.obscuration.R_inner,
                            xy_outer=self.ofc_data.config.obscuration.R_outer,
                        ).rotate(theta_uv=rotation_angle)(field_x, field_y)
                    ]
                )
                for dof_idx in self.ofc_data.dof_idx
            ]
        )

        # Reshape the sensitivity matrix to be (#field_points, #zernikes, #dofs)
        rotated_sensitivity_matrix = np.einsum('ijk->jki', rotated_sensitivity_matrix)

        # Subselect the relevant zernike coefficients
        # to include in the sensitivity matrix.
        rotated_sensitivity_matrix = rotated_sensitivity_matrix[
            :, self.ofc_data.znmin : self.ofc_data.znmax + 1, :
        ]

        return rotated_sensitivity_matrix, field_idx