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
import galsim
from scipy.linalg import block_diag
import lsst.obs.lsst as obs_lsst
from lsst.afw.cameraGeom import FIELD_ANGLE


class SensitivityMatrix:
    """Handle camera rotation.

    Attributes
    ----------
    rot : `float`
        Camera rotator angle in degrees.
    """

    def __init__(self, ofc_data):
        self.ofc_data = ofc_data
        
    def evaluate_sensitivity(self, rotation_angle, sensor_names):

        field_idx = np.array(
            [
                self.ofc_data.field_idx[sensor_name]
                for sensor_name in sensor_names
            ]
        )

        if not self.ofc_data.double_zernikes:
            # Get the field indices for the sensors
            sen_m = self.ofc_data.sensitivity_matrix[
                np.ix_(
                    np.arange(self.ofc_data.sensitivity_matrix.shape[0]),
                    np.arange(self.ofc_data.sensitivity_matrix.shape[1]),
                    self.ofc_data.dof_idx,
                )
            ]

            return sen_m[field_idx, :, :]

        camera = obs_lsst.LsstCam().getCamera()
        fieldList = []
        for name in sensor_names:
            centerPt = camera.get(name).getCenter(FIELD_ANGLE)
            fieldList.append( ( np.degrees(centerPt[1]), np.degrees(centerPt[0]) ))
        field_x, field_y = zip(*fieldList)

        rotated_sensitivity_matrix = np.array([
            np.array([
                zk.coef
                for zk in galsim.zernike.DoubleZernike(
                    self.ofc_data.sensitivity_matrix[:, :, dof_idx],
                    # Rubin annuli
                    uv_inner=0.0, uv_outer=1.75,
                    xy_inner=0.612*4.18, xy_outer=4.18
                ).rotate(theta_uv=rotation_angle)(field_x, field_y)
            ])
            for dof_idx in self.ofc_data.dof_idx
        ])

        rotated_sensitivity_matrix = np.moveaxis(rotated_sensitivity_matrix, 0, -1)


        rotated_sensitivity_matrix = rotated_sensitivity_matrix[:, self.ofc_data.znmin:self.ofc_data.znmax + 1, :]


        return rotated_sensitivity_matrix, field_idx
