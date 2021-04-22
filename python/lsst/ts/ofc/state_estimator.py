# This file is part of ts_ofc.
#
# Developed for the LSST Telescope and Site Systems.
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
    """

    RCOND = 1e-4

    def __init__(self, ofc_data, log=None):

        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        self.ofc_data = ofc_data

    def dof_state(self, filter_name, wfe, field_idx):
        """Compute the state in the basis of degrees of freedom.

        Solve y = A*x by x = pinv(A)*y.

        Parameters
        ----------
        filter_name : `string`
            Name of the filter. Must be in `self.intrinsic_zk`.
        wfe : `numpy.ndarray`
            Wavefront error im um.
        field_idx : `numpy.ndarray` or `list` of `int`
            Field index array.

        Returns
        -------
        numpy.ndarray
            Optical state in the basis of DOF.
        """

        # Constuct the sensitivity matrix A

        mat_a = self.ofc_data.sensitivity_matrix[
            np.ix_(
                np.arange(self.ofc_data.sensitivity_matrix.shape[0]),
                self.ofc_data.zn3_idx,
                self.ofc_data.dof_idx,
            )
        ]

        size_ = mat_a.shape[2]

        mat_a = mat_a[field_idx, :, :]

        mat_a = mat_a.reshape((-1, size_))

        # Check the dimension of pinv A
        num_zk, num_dof = mat_a.shape
        if num_zk < num_dof:
            raise RuntimeError(
                f"Equation number ({num_zk}) < variable number ({num_dof})."
            )

        pinv_a = np.linalg.pinv(mat_a, rcond=self.RCOND)

        a = np.array(wfe)[:, self.ofc_data.zn3_idx]
        b = self.ofc_data.get_intrinsic_zk(filter_name, field_idx)
        c = self.ofc_data.y2_correction[np.ix_(field_idx, self.ofc_data.zn3_idx)]

        y = a - b - c

        y = y.reshape(-1, 1)

        x = pinv_a.dot(y)

        return x.ravel()
