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
import lsst.obs.lsst as obs_lsst
from lsst.afw.cameraGeom import FIELD_ANGLE


class SensitivityMatrix:
    """Class to handle the sensitivity matrix.

    Parameters
    ----------
    ofc_data : `lsst.ts.ofc.ofc_data.OFCData`
        OFC data.
    """

    def __init__(self, ofc_data) -> None:
        self.ofc_data = ofc_data

    def evaluate_sensitivity(
        self, rotation_angle: float, sensor_names: None | list = None
    ) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """Evaluate the sensitivity matrix for a given rotation angle.

        Parameters
        ----------
        rotation_angle : `float`
            Rotation angle in degrees.
        sensor_names : `list` of `str`, optional
            List of sensor names. If None, uses all the GQ points are used.

        Returns
        -------
        `np.array` of `float`
            Sensitivity matrix for the given rotation angle.
        `np.array` of `int`
            Field indices for the sensors.
        """

        # If sensor_names is None getsensitivity matrix at all GQ points
        if sensor_names is None:
            # Create array for all the GQ points
            field_idx = np.arange(self.ofc_data.gq_field_angles.shape[0])
            # Retrieve field angles for each GQ point from ofc_data
            field_x, field_y = zip(*self.ofc_data.gq_field_angles)

        else:
            # Obtain the field indices for the sensors
            field_idx = np.array(
                [self.ofc_data.field_idx[sensor_name] for sensor_name in sensor_names]
            )
            # Get the field angles for the sensors
            field_x, field_y = get_field_angle(sensor_names)

        # If not using double zernikes, use the stored GQ sensitivity matrix
        if not self.ofc_data.double_zernikes:
            # Get the sensitivity matrix
            sen_m = self.ofc_data.sensitivity_matrix[
                np.ix_(
                    np.arange(self.ofc_data.sensitivity_matrix.shape[0]),
                    np.arange(self.ofc_data.sensitivity_matrix.shape[1]),
                    self.ofc_data.dof_idx,
                )
            ]

            # return the sensitivity matrix at the given field indices.
            return sen_m[field_idx, :, :], field_idx

        # If using double zernikes, compute the sensitvity mat
        # using galsim DoubleZernikes
        rotated_sensitivity_matrix = np.array(
            [
                np.array(
                    [
                        zk.coef
                        for zk in galsim.zernike.DoubleZernike(
                            self.ofc_data.sensitivity_matrix[:, :, dof_idx],
                            # Rubin annuli
                            uv_inner=0.0,
                            uv_outer=1.75,
                            xy_inner=0.612 * 4.18,
                            xy_outer=4.18,
                        ).rotate(theta_uv=rotation_angle)(field_x, field_y)
                    ]
                )
                for dof_idx in self.ofc_data.dof_idx
            ]
        )
        # Reshape the sensitivity matrix to have the
        # same shape as the one stored.
        rotated_sensitivity_matrix = np.moveaxis(rotated_sensitivity_matrix, 0, -1)

        # Subselect the relevant zernike coefficients
        # to include in the sen matrix.
        rotated_sensitivity_matrix = rotated_sensitivity_matrix[
            :, self.ofc_data.znmin : self.ofc_data.znmax + 1, :
        ]

        return rotated_sensitivity_matrix, field_idx


def get_field_angle(sensor_names: list) -> Tuple[List[float], List[float]]:
    """Get the field angle for a given sensor name.

    Parameters
    ----------
    sensor_names : `list` of `str`
        List of sensor names.

    Returns
    -------
    field_x : `list` of `float`
        List of field x angles in degrees.
    field_y : `list` of `float`
        List of field y angles in degrees.
    """

    # Create camera object
    camera = obs_lsst.LsstCam().getCamera()

    # Get the field angle for each sensor
    fieldList = []
    for name in sensor_names:
        centerPt = camera.get(name).getCenter(FIELD_ANGLE)
        fieldList.append((np.degrees(centerPt[1]), np.degrees(centerPt[0])))

    # Return the field angles field_x and field_y
    return zip(*fieldList)
