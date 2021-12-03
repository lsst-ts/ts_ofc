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

import logging

import numpy as np


class KalmanFilter:
    """Kalman Filter Update.

    This class is used to determine the Kalman Filter update of degree of
    freedom (DOF) at time `k+1` based on the wavefront error (`yk`) at time
    `k` and the DOF at time `k`.

    Parameters
    ----------
    ofc_data : `OFCData`
        Data container.
    log : `logging.Logger` or `None`
        Optional logging class to be used for logging operations. If `None`,
        creates a new logger.

    Attributes
    ----------
    Rk : `np.array`
        Covariance of observation noise (wfe = sen_m*dof + obs_noise).
        Dim = (9, 19, 19)
    Kk : `np.array`
        Kalman filter gain.
        Dim = (50, 19)
    log : `logging.Logger`
        Logger class used for logging operations.
    n_imqw : `np.array`
        Array of image quality weights.
        Dim = (9,)
    ofc_data : `OFCData`
        OFC data container.
    Qk : `np.array`
        Covariance of process noise. 
        Dim = (50, 50)
    Pkk : `np.array`
        A posteriori estimate covariance matrix. cov(dof - dof_estimated).
        Dim = (50, 50)
    sen_m : `np.array`
        Sensitivity matrix.
        Dim = (9, 19, 50)
    Sk : `np.array`
        Innovation covariance. Covariance of the estimation error (wfe - sen_m*optical_state) 
        Dim = (9, 19, 19)
    """

    def __init__(self, ofc_data, log=None):

        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        self.ofc_data = ofc_data

        # Initialize weightx vector
        self.n_imqw = self.ofc_data.normalized_image_quality_weight

        # Initialize sensitivity matrix
        self.sen_m = self.ofc_data.sensitivity_matrix[
            np.ix_(
                np.arange(self.ofc_data.sensitivity_matrix.shape[0]),
                np.arange(self.ofc_data.sensitivity_matrix.shape[1]),
                self.ofc_data.dof_idx,
            )
        ]

        # Initialize error covariances matrices
        self.Rk = np.zeros((self.sen_m.shape[1], self.sen_m.shape[1]))
        self.Qk = 0.005*np.identity(len(self.ofc_data.dof_idx))

        # Initializes kalman covariances and gain.
        self.Sk = np.zeros((self.sen_m.shape[0], self.sen_m.shape[1], self.sen_m.shape[1]))
        self.Pkk = 0.005*np.identity(len(self.ofc_data.dof_idx))
        self.Kk = np.zeros( (len(self.ofc_data.dof_idx), self.sen_m.shape[1]) )

    def update(self, wfe, optical_state):
        """Compute the Kalman filter update.
        """
        # Update Kalman filter gain and covariances.
        self.update_gain(wfe, optical_state)

        # Compute new measurement residual.
        res = self.residual(wfe, optical_state)

        return self.Kk@res

    def residual(self, wfe, optical_state):
        """Compute the averaged measurement residual given the current estimated optical state.
        """
        optical_state = optical_state.reshape(-1, 1)
        res = 0

        for a_mat, wgt, wf in zip(self.sen_m, n_imqw, wfe):
            wf = wf.reshape(-1, 1)
            res += wgt * (wf - a_mat@optical_state)

        return res

    def update_gain(self, wfe, optical_state):
        """Update Kalman filter gain and covariances.

        Parameters
        ----------
        dof : `numpy.ndarray` or `list`
            Calculated DOF.
        dof_idx : `numpy.ndarray` or `list` of `int`
            Index array of degree of freedom.
        """
        # Compute new covariance
        Pk_prev = self.Pkk + self.Qk
        
        # Compute innovation matrix.
        self.Sk = self.Rk + self.sen_m @ Pk_prev @ self.sen_m.transpose((0, 2, 1))
        Sinv = np.linalg.inv(self.Sk)
 
        # Update Optimal Kalman filter
        K_prev = np.zeros(self.Kk.shape)
        for sen_m, wgt, S in zip(self.sen_m, n_imqw, Sinv):
            K_prev += wgt * (Pk_prev @ sen_m.T @ S)
        self.Kk = K_prev

        # Update covariance
        Pkk_prev = np.zeros(self.Pkk.shape)
        for sen_m, wgt in zip(self.sen_m, n_imqw):
            Pkk_prev += wgt * (np.identity(len(optical_state)) - self.Kk @ sen_m) @ Pk_prev
        self.Pkk = Pkk_prev