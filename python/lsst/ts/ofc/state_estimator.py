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

import galsim
import numpy as np
from scipy.linalg import fractional_matrix_power

from . import SensitivityMatrix
from .ofc_data import OFCData
from .utils.ofc_data_helpers import get_intrinsic_zernikes

RCOND_NOISE_COV = 1e-9


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
        self.noise_covariance = ofc_data.noise_covariance

        self.rcond = ofc_data.controller.get("truncation_threshold", None)
        self.truncate_index = ofc_data.controller.get("truncation_index", None)

    def get_normalization_matrix(self) -> np.ndarray[float]:
        """Get the normalization matrix.

        The normalization is defined in Eqs 9-11 of
        https://ui.adsabs.harvard.edu/abs/2024ApJ...974..108M

        Returns
        -------
        numpy.ndarray
            Normalization matrix.
        """
        return np.diag(self.normalization_weights[self.ofc_data.dof_idx])

    def get_sensitivity_matrix(
        self,
        field_angles: list,
        rotation_angle: float,
        normalize: bool = False,
        truncate: bool = False,
        check_invertible: bool = True,
    ) -> np.ndarray[float]:
        """Get the sensitivity matrix at the sensor positions.

        The normalization is defined in Eqs 9-11 and the truncation in Eqs 2-7
        of https://ui.adsabs.harvard.edu/abs/2024ApJ...974..108M

        Parameters
        ----------
        field_angles : `list`
            List of field angles at which to evaluate the sensitivity matrix.
        rotation_angle : `float`
            Rotation angle in degrees.
        normalize : `bool`
            Whether to normalize the sensitivity matrix.
            Default is `False`.
        truncate : `bool`
            Whether to truncate the sensitivity matrix.
            Default is `False`.
        check_invertible : `bool`
            Whether to check if the sensitivity matrix is invertible.
            Default is `True`.

        Returns
        -------
        numpy.ndarray
            Sensitivity matrix at the sensor positions.
        """
        # Get the field angles for the sensors
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

        if normalize:
            normalization_matrix = self.get_normalization_matrix()
            sensitivity_matrix = sensitivity_matrix @ normalization_matrix

        # Check the dimension of sensitivity matrix to see if we can invert it
        num_zk, num_dof = sensitivity_matrix.shape
        if num_zk < num_dof and check_invertible:
            raise RuntimeError(f"Equation number ({num_zk}) < variable number ({num_dof}).")

        if truncate:
            # Compute the pseudo-inverse of the sensitivity matrix
            # rcond sets the truncation of different modes.
            # If rcond is None, it is computed from the singular values
            # of the sensitivity matrix, using truncation index as reference.
            if self.rcond is None and self.truncate_index is None:
                raise ValueError("Neither truncation index or threshold are set in the controller.")

            # Handle truncation of the sensitivity matrix using SVD first.
            # This ensures the v-modes will not depend on the noise covariance.
            u, s, vh = np.linalg.svd(sensitivity_matrix, full_matrices=False)
            if self.truncate_index is not None:
                self.log.info("Setting rcond value from truncation index.")
                if self.truncate_index >= len(s):
                    self.rcond = 0.99 * s[-1] / np.max(s)
                else:
                    self.rcond = 0.99 * s[self.truncate_index - 1] / np.max(s)

            cutoff = self.rcond * np.amax(s, axis=-1, keepdims=True)
            large = s > cutoff
            s[~large] = 0
            sensitivity_matrix = u @ np.diag(s) @ vh

        return sensitivity_matrix

    def get_noise_covariance(self, sensor_names: list) -> np.ndarray[float]:
        """Get the noise covariance matrix.

        Parameters
        ----------
        sensor_names : `list`
            List of sensor names.

        Returns
        -------
        numpy.ndarray
            Noise covariance matrix.
        """
        n_zernikes = self.ofc_data.znmax - self.ofc_data.znmin + 1
        n_sensors_cov = self.noise_covariance.shape[0] // n_zernikes
        if len(sensor_names) != n_sensors_cov:
            if len(sensor_names) < n_sensors_cov:
                self.log.warning(
                    f"Number of sensors ({len(sensor_names)}) less than "
                    f"the noise covariance sensor matrix size ({n_sensors_cov}). "
                    "This mode is not supported yet, so an identity matrix "
                    "will be used for now."
                )
                noise_covariance_eval = np.eye(len(sensor_names) * n_zernikes)
            else:
                raise ValueError(
                    f"Number of sensors ({len(sensor_names)}) exceeds "
                    f"the noise covariance sensor matrix size ({n_sensors_cov})."
                )
        else:
            noise_covariance_eval = self.noise_covariance

        full_idx = np.concatenate(
            [
                self.ofc_data.zn_idx + i * (self.ofc_data.znmax - self.ofc_data.znmin + 1)
                for i in range(len(sensor_names))
            ]
        )
        used_noise_covariance = noise_covariance_eval[np.ix_(full_idx, full_idx)]

        return used_noise_covariance

    def dof_state(
        self,
        filter_name: str,
        wfe: np.ndarray[float],
        sensor_names: list,
        rotation_angle: float,
        subtract_intrinsics: bool = True,
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
        subtract_intrinsics : `bool`, optional
            Whether to subtract the intrinsic wavefront errors from the
            measured wavefront errors. Default is `True`.

        Returns
        -------
        numpy.ndarray
            Optical state in the basis of DOF.
        """
        # Get (truncated, normalized) sensitivity at sensor positions
        field_angles = [self.ofc_data.sample_points[sensor] for sensor in sensor_names]
        sensitivity_matrix = self.get_sensitivity_matrix(
            field_angles,
            rotation_angle,
            normalize=True,
            truncate=True,
        )

        # Calculate inverse of noise covariance for sensors
        noise_covariance = self.get_noise_covariance(sensor_names)
        noise_cov_inv_sqrt = fractional_matrix_power(noise_covariance, -0.5)

        # With the truncated sensitivity matrix, now include noise covariance
        # when computing the pseudo-inverse. We use the 1e-9 default rcond.
        pinv_sensitivity_matrix = np.linalg.pinv(
            noise_cov_inv_sqrt @ sensitivity_matrix, rcond=RCOND_NOISE_COV
        )

        # Rotate the wavefront error to the same orientation as the
        # sensitivity matrix. When creating galsim.Zernike object,
        # the coefficients are in units of um which does not matter
        # here as we are only rotating them.
        # Note that we need to pad the wfe with zeros for the 4 first
        # Zernike coefficients, since wfe starts with Z4
        wfe = np.array(wfe)
        for idx in range(wfe.shape[0]):
            wfe_sensor = np.pad(wfe[idx, :], (self.ofc_data.znmin, 0))

            zk_galsim = galsim.zernike.Zernike(
                wfe_sensor,
                R_outer=self.ofc_data.config["pupil"]["radius_outer"],
                R_inner=self.ofc_data.config["pupil"]["radius_inner"],
            )
            # Note that we need to remove the first 4 Zernike coefficients
            # since we padded the wfe with zeros for the 4 first Zernike
            wfe[idx, :] = zk_galsim.rotate(np.deg2rad(rotation_angle)).coef[self.ofc_data.znmin :]

        self.log.debug(f"Derotated wavefront error: {wfe}")
        # Compute wavefront error deviation from the intrinsic wavefront error
        # y = wfe - intrinsic_zk - y2_correction
        # y2_correction is a static correction for the
        # deviation currently set to zero.
        y2_correction = np.array([self.ofc_data.y2_correction[sensor] for sensor in sensor_names])
        if subtract_intrinsics:
            self.log.info("Subtracting intrinsic wavefront errors from measured wavefront errors.")
            y = (
                wfe[:, self.ofc_data.zn_idx]
                - get_intrinsic_zernikes(self.ofc_data, filter_name, sensor_names, rotation_angle)[
                    :, self.ofc_data.zn_idx
                ]
                - y2_correction[:, self.ofc_data.zn_idx]
            )
        else:
            y = wfe[:, self.ofc_data.zn_idx] - y2_correction[:, self.ofc_data.zn_idx]

        # Reshape wavefront error to dimensions
        # (#zk * #sensors, 1) = (19 * #sensors, 1)
        y = y.reshape(-1, 1)

        # Compute optical state estimate in the basis of DOF
        # Because of normalization, we need to de-normalize the result
        # to retrieve the actual DOF values in the original 50 dimensional
        # basis. For more details, see equation (10) in arXiv:2406.04656.
        # For the noise covariance part, see description in SITCOMTN-129.
        normalization_matrix = self.get_normalization_matrix()
        x = normalization_matrix @ pinv_sensitivity_matrix @ noise_cov_inv_sqrt @ y

        return x.ravel()
