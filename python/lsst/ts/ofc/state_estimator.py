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

__all__ = ["StateEstimator"]

import logging

import numpy as np

from . import SensitivityMatrix
from .ofc_data import OFCData


class StateEstimator:
    """(Optical) State Estimator.

    Estimate the state of the optics in the basis of the degree of freedom
    (DOF).

    Parameters
    ----------
    ofc_data : `OFCData`
        Data container.
    log : `logging.Logger` or `None`
        Optional logging class to be used for logging operations. If `None`,
        creates a new logger.

    Attributes
    ----------
    log : `logging.Logger`
        Logger class used for logging operations.
    ofc_data : `OFCData`
        OFC data container.
    RCOND : `float`
        Cutoff for small singular values, used when computing pseudo-inverse
        matrix.
    """

    def __init__(self, ofc_data: OFCData, log: logging.Logger | None = None) -> None:
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        self.ofc_data = ofc_data

        # Constuct the double zernike sensitivity matrix
        self.dz_sensitivity_matrix = SensitivityMatrix(self.ofc_data)

        self.normalization_weights = ofc_data.normalization_weights

        self.rcond = ofc_data.controller.get("truncation_threshold", None)
        self.truncate_index = ofc_data.controller.get("truncation_index", None)

    def dof_state(
        self,
        filter_name: str,
        wfe: np.ndarray[float],
        sensor_names: list,
        rotation_angle: float,
    ) -> np.ndarray[float]:
        """Compute the state in the basis of degrees of freedom.

        Solve y = A*x by x = pinv(A)*y.

        Parameters
        ----------
        filter_name : `string`
            Name of the filter. Must be in `self.intrinsic_zk`.
        wfe : `numpy.ndarray`
            Wavefront error im um.
        sensor_names : `list`
            List of sensor names.
        rotation_angle : `float`
            Rotation angle in degrees.

        Returns
        -------
        numpy.ndarray
            Optical state in the basis of DOF.
        """

        # Get the field angles for the sensors
        field_angles = [self.ofc_data.sample_points[sensor] for sensor in sensor_names]
        field_x, field_y = zip(*field_angles)

        rotation_angle_rad = np.deg2rad(-rotation_angle)
        rot_mat = np.array(
            [
                [np.cos(rotation_angle_rad), -np.sin(rotation_angle_rad)],
                [np.sin(rotation_angle_rad), np.cos(rotation_angle_rad)],
            ]
        )
        field_angles = np.array([field_x, field_y]).T @ rot_mat

        # Evaluate sensitivity matrix at sensor positions
        # The rotation angle is negative because the rotation
        # in the uv-plane for the Double Zernike object
        # needs to be in the opposite direction.
        sensitivity_matrix = self.dz_sensitivity_matrix.evaluate(field_angles, 0.0)

        # Select sensitivity matrix only at used degrees of freedom
        sensitivity_matrix = sensitivity_matrix[:, self.ofc_data.zn_idx, :]

        # Reshape sensitivity matrix to dimensions
        # (#zk * #sensors, # dofs) = (19 * #sensors, 50)
        size = sensitivity_matrix.shape[2]
        sensitivity_matrix = sensitivity_matrix.reshape((-1, size))

        # Select sensitivity matrix only at used degrees of freedom
        sensitivity_matrix = sensitivity_matrix[..., self.ofc_data.dof_idx]

        normalization_matrix = np.diag(
            self.normalization_weights[self.ofc_data.dof_idx]
        )
        sensitivity_matrix = sensitivity_matrix @ normalization_matrix

        # Check the dimension of sensitivity matrix to see if we can invert it
        num_zk, num_dof = sensitivity_matrix.shape
        if num_zk < num_dof:
            raise RuntimeError(
                f"Equation number ({num_zk}) < variable number ({num_dof})."
            )

        # Compute the pseudo-inverse of the sensitivity matrix
        # rcond sets the truncation of different modes.
        # If rcond is None, it is computed from the singular values
        # of the sensitivity matrix, using the truncation index as reference.
        if self.rcond is None and self.truncate_index is None:
            raise ValueError(
                "Neither truncation index or threshold are set in the controller."
            )

        if self.truncate_index is not None:
            self.log.info("Setting rcond value from truncation index.")
            _, s, _ = np.linalg.svd(sensitivity_matrix, full_matrices=False)
            if self.truncate_index >= len(s):
                self.rcond = 0.99 * s[-1] / np.max(s)
            else:
                self.rcond = 0.99 * s[self.truncate_index - 1] / np.max(s)

        pinv_sensitivity_matrix = np.linalg.pinv(sensitivity_matrix, rcond=self.rcond)

        # Reshape wavefront error to dimensions
        # (#zk * #sensors, 1) = (19 * #sensors, 1)
        y = wfe.reshape(-1, 1)

        # Compute optical state estimate in the basis of DOF
        # Because of normalization, we need to de-normalize the result
        # to retrieve the actual DOF values in the original 50 dimensional
        # basis. For more details, see equation (10) in arXiv:2406.04656.
        x = normalization_matrix @ pinv_sensitivity_matrix.dot(y)

        return x.ravel()
