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

    def __init__(
        self, ofc_data: OFCData, rcond: int = 1e-4, log: logging.Logger = None
    ) -> None:
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        self.ofc_data = ofc_data

        # Set rcond for the pseudoinverse computation
        self.rcond = rcond

    def dof_state(
        self,
        filter_name: str,
        wfe: np.ndarray,
        field_idx: np.ndarray,
        rotation_angle: float,
    ) -> np.ndarray:
        """Compute the state in the basis of degrees of freedom.

        Solve y = A*x by x = pinv(A)*y.

        Parameters
        ----------
        filter_name : `string`
            Name of the filter. Must be in `self.intrinsic_zk`.
        wfe : `numpy.ndarray`
            Wavefront error im um.
        field_idx : `numpy.ndarray`
            Field indices for the sensors.
        rotation_angle : `float`
            Rotation angle in degrees.

        Returns
        -------
        numpy.ndarray
            Optical state in the basis of DOF.
        """

        # Constuct the double zernike sensitivity matrix
        dz_sensitivity_matrix = SensitivityMatrix(self.ofc_data)

        # Evaluate sensitivity matrix at sensor positions
        sensitivity_matrix = dz_sensitivity_matrix.evaluate(rotation_angle, field_idx)

        # Select sensitivity matrix only at used degrees of freedom
        sensitivity_matrix = sensitivity_matrix[:, self.ofc_data.zn3_idx, :]

        # Reshape sensitivity matrix to dimensions
        # (#zk * #sensors, # dofs) = (19 * #sensors, 50)
        size_ = sensitivity_matrix.shape[2]
        sensitivity_matrix = sensitivity_matrix.reshape((-1, size_))

        # Select sensitivity matrix only at used degrees of freedom
        sensitivity_matrix = sensitivity_matrix[..., self.ofc_data.dof_idx]

        # Check the dimension of sensitivity matrix to see if we can invert it
        num_zk, num_dof = sensitivity_matrix.shape
        if num_zk < num_dof:
            raise RuntimeError(
                f"Equation number ({num_zk}) < variable number ({num_dof})."
            )

        # Compute the pseudo-inverse of the sensitivity matrix
        # rcond sets the truncation of different modes.
        pinv_sensitivity_matrix = np.linalg.pinv(sensitivity_matrix, rcond=self.rcond)

        # Rotate the wavefront error to the same orientation as the
        # sensitivity matrix. When creating galsim.Zernike object,
        # the coefficients are in units of um which does not matter
        # here as we are only rotating them.
        wfe = np.array(wfe)
        for idx in range(wfe.shape[0]):
            wfe_sensor = np.pad(wfe[idx, :], (4, 0))

            zk_galsim = galsim.zernike.Zernike(
                wfe_sensor,
                R_outer=self.ofc_data.config["obscuration"]["R_outer"],
                R_inner=self.ofc_data.config["obscuration"]["R_inner"],
            )
            wfe[idx, :] = zk_galsim.rotate(np.deg2rad(rotation_angle)).coef[4:]

        # Compute wavefront error deviation from the intrinsic wavefront error
        # y = wfe - intrinsic_zk - y2_correction
        # y2_correction is a static correction for the
        # deviation currently set to zero.
        y = (
            wfe[:, self.ofc_data.zn3_idx]
            - self.ofc_data.get_intrinsic_zk(filter_name, field_idx, rotation_angle)[
                :, self.ofc_data.zn3_idx
            ]
            - self.ofc_data.y2_correction[np.ix_(field_idx, self.ofc_data.zn3_idx)]
        )

        # Reshape wavefront error to dimensions
        # (#zk * #sensors, 1) = (19 * #sensors, 1)
        y = y.reshape(-1, 1)

        # Compute optical state estimate in the basis of DOF
        x = pinv_sensitivity_matrix.dot(y)

        return x.ravel()
