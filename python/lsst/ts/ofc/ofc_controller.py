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

from . import BendModeToForce


class OFCController:
    """Optical Feedback Control Controller.

    This class is mainly used to determine the offset (`uk`) of degree of
    freedom (DOF) at time `k+1` based on the wavefront error (`yk`) at time
    `k`.

    Parameters
    ----------
    ofc_data : `OFCData`
        Data container.
    log : `logging.Logger` or `None`
        Optional logging class to be used for logging operations. If `None`,
        creates a new logger.

    Attributes
    ----------
    dof_state : `np.array`
        State of telescope in the basis of degrees of freedom.
    dof_state0 : `np.array`
        Initial state of telescope in the basis of degrees of freedom.
    log : `logging.Logger`
        Logger class used for logging operations.
    m1m3_bmf : `BendModeToForce`
        Class to convert bend mode to forces for M1M3.
    m2_bmf : `BendModeToForce`
        Class to convert bend mode to forces for M2.
    ofc_data : `OFCData`
        OFC data container.
    """

    # Eta in FWHM calculation.
    ETA = 1.086

    # FWHM in atmosphere.
    FWHM_ATM = 0.6

    def __init__(self, ofc_data, log=None):
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        self.ofc_data = ofc_data

        self.m1m3_bmf = BendModeToForce("M1M3", self.ofc_data)
        self.m2_bmf = BendModeToForce("M2", self.ofc_data)

        self._gain = 0

        self.dof_state0 = np.zeros(len(self.ofc_data.dof_idx))

        for comp in self.ofc_data.comp_dof_idx:
            start_idx = self.ofc_data.comp_dof_idx[comp]["startIdx"]
            end_idx = (
                self.ofc_data.comp_dof_idx[comp]["startIdx"]
                + self.ofc_data.comp_dof_idx[comp]["idxLength"]
            )

            state0name = self.ofc_data.comp_dof_idx[comp]["state0name"]

            if "Hexapod" in state0name:
                self.dof_state0[start_idx:end_idx] = np.array(
                    [
                        self.ofc_data.dof_state0[state0name][axis_name]
                        for axis_name in ["dZ", "dX", "dY", "rX", "rY"]
                    ]
                )
            else:
                self.dof_state0[start_idx:end_idx] = np.array(
                    [
                        self.ofc_data.dof_state0[state0name][f"mode{mode_idx+1}"]
                        for mode_idx in range(
                            self.ofc_data.comp_dof_idx[comp]["idxLength"]
                        )
                    ]
                )

        self.dof_state = self.dof_state0.copy()

    def reset_dof_state(self):
        """Initialize the state to the state 0 in the basis of degree of
        freedom (DOF).
        """

        self.dof_state = self.dof_state0.copy()

    def aggregate_state(self, dof, dof_idx):
        """Aggregate the calculated degree of freedom (DOF) in the state.

        Parameters
        ----------
        dof : `numpy.ndarray` or `list`
            Calculated DOF.
        dof_idx : `numpy.ndarray` or `list` of `int`
            Index array of degree of freedom.
        """

        self.dof_state[dof_idx] += dof

    @property
    def aggregated_state(self):
        """Returns the aggregated state.

        Returns
        -------
        `np.ndarray`
            Aggregated state.
        """
        return self.dof_state[self.ofc_data.dof_idx]

    @property
    def gain(self):
        """Get the gain value.

        Returns
        -------
        gain : `float`
            Gain value in the feedback.
        """

        return self._gain

    @gain.setter
    def gain(self, value):
        """Set the gain value.

        Parameters
        ----------
        value : `float`
            Gain value in the feedback. It should be in the range of 0 and 1.

        Raises
        ------
        ValueError
            if value is not in the range of [0, 1].
        """

        if 0.0 <= value <= 1.0:
            self._gain = value
        else:
            raise ValueError(f"Gain must be in the range of [0, 1]. Got {value}.")

    def authority(self):
        """Compute the authority of the system.

        Returns
        -------
        authority : `np.array`
        """

        # Rigid Body Stroke - Authority
        rbs_authority = self.ofc_data.rb_stroke[0] / self.ofc_data.rb_stroke

        m1m3_authority = np.std(self.m1m3_bmf.rot_mat, axis=0)

        m2_authority = np.std(self.m2_bmf.rot_mat, axis=0)

        authority = np.concatenate(
            (
                rbs_authority,
                self.ofc_data.m1m3_actuator_penalty * m1m3_authority,
                self.ofc_data.m2_actuator_penalty * m2_authority,
            )
        )

        return authority

    def calc_uk_x00(self, mat_f, qx, mat_h):
        """Calculate uk by referencing to "x00".
        The offset will only trace the relative changes of offset without
        regarding the real value.
        uk = -F' * [QX + rho**2 * H * (S - S0)].

        Parameters
        ----------
        mat_f : `numpy.ndarray`
            Matrix F.
        qx : `numpy.ndarray`
            qx array.

        Returns
        -------
        `numpy.ndarray`
            Calculated uk in the basis of degree of freedom (DOF).
        """
        state_diff = (
            self.dof_state[self.ofc_data.dof_idx]
            - self.dof_state0[self.ofc_data.dof_idx]
        )
        state_diff = state_diff.reshape(-1, 1)

        _qx = qx + self.ofc_data.motion_penalty**2 * mat_h.dot(state_diff)

        return self.calc_uk_x0(mat_f=mat_f, qx=_qx)

    def calc_uk_x0(self, mat_f, qx, **kwargs):
        """Calculate uk by referencing to "x0".

        The offset will only trace the previous one.

        uk = -F' * QX.

        Parameters
        ----------
        mat_f : `numpy.ndarray`
            Matrix F.
        qx : `numpy.ndarray`
            qx array.
        kwargs : `dict`
            Additional keyword arguments. This is mainly added to provide
            similar interaface to other `calc_uk_*` methods.

        Returns
        -------
        uk : `numpy.ndarray`
            Calculated uk in the basis of degree of freedom (DOF).
        """
        return -mat_f.dot(qx)

    def calc_uk_0(self, mat_f, qx, mat_h):
        """Calculate uk by referencing to "0".

        The offset will trace the real value and target for 0.

        uk = -F' * (QX + rho**2 * H * S).

        Parameters
        ----------
        mat_f : `numpy.ndarray`
            Matrix F.
        qx : `numpy.ndarray`
            qx array.
        mat_h : `numpy.ndarray`
            The H matrix (see equation above).

        Returns
        -------
        uk : `numpy.ndarray`
            Calculated uk in the basis of degree of freedom (DOF).
        """
        state = self.dof_state.reshape(-1, 1)

        _qx = qx + self.ofc_data.motion_penalty**2 * mat_h.dot(state)

        return self.calc_uk_x0(mat_f=mat_f, qx=_qx)

    def uk_gain(self, filter_name, dof_state):
        """Estimate uk in the basis of degree of freedom (DOF) with gain
        compensation.

        Parameters
        ----------
        filter_name : `string`
            Name of the filter.
        dof_state : `numpy.ndarray`
            Optical state in the basis of DOF.

        Returns
        -------
        uk : `numpy.ndarray`
            Calculated uk in the basis of DOF.
        """

        return self.gain * self.uk(filter_name, dof_state)

    def uk(self, filter_name, dof_state):
        """Estimate the offset (`uk`) of degree of freedom (DOF) at time `k+1`
        based on the wavefront error (`yk`) at time `k`.

        uk in the basis of degree of freedom (DOF) without gain
        compensation.

        Parameters
        ----------
        filter_name : `string`
            Name of the filter.
        dof_state : `numpy.ndarray`
            Optical state in the basis of DOF.

        Returns
        -------
        uk : `numpy.ndarray`
            Calculated uk in the basis of DOF.

        Raises
        ------
        RuntimeError
            If `xref` strategy is not valid.
        """
        if self.ofc_data.xref not in self.ofc_data.xref_list:
            raise RuntimeError(
                f"Unspecified reference frame {self.ofc_data.xref}. "
                f"Must be one of {self.ofc_data.xref_list}."
                "Check ofc_data configuration."
            )

        # Calculate CC matrix
        # Cost function: J = x.T * Q * x + rho * u.T * H * u.
        # Choose x.T * Q * x = p.T * p
        # p = C * y = C * (A * x)
        # p.T * p = (C * A * x).T * C * A * x
        #         = x.T * (A.T * C.T * C * A) * x = x.T * Q * x
        # CCmat is C.T *C above.

        cc_mat = (
            2.0 * np.pi / self.ofc_data.eff_wavelength[filter_name]
        ) ** 2.0 * self.ofc_data.alpha[self.ofc_data.zn3_idx]
        cc_mat = np.diag(cc_mat)

        # Calculate the Qx.
        #
        # Qx = sum_{wi * A.T * C.T * C * (A * yk + y2k)}.

        _dof_state = dof_state.reshape(-1, 1)

        n_imqw = self.ofc_data.normalized_image_quality_weight
        sen_m = self.ofc_data.sensitivity_matrix[
            np.ix_(
                np.arange(self.ofc_data.sensitivity_matrix.shape[0]),
                np.arange(self.ofc_data.sensitivity_matrix.shape[1]),
                self.ofc_data.dof_idx,
            )
        ]

        y2c = self.ofc_data.y2_correction[np.arange(len(n_imqw))]

        qx = 0
        q_mat = 0
        for a_mat, wgt, y2k in zip(sen_m, n_imqw, y2c):
            y2k = y2k.reshape(-1, 1)
            qx += wgt * a_mat.T.dot(cc_mat).dot(a_mat.dot(_dof_state) + y2k)
            q_mat += wgt * a_mat.T.dot(cc_mat).dot(a_mat)

        # Calculate the F matrix.
        #
        # F = inv(A.T * C.T * C * A + rho * H).

        authority = self.authority()
        dof_idx = self.ofc_data.dof_idx
        mat_h = np.diag(authority[dof_idx] ** 2)

        mat_f = np.linalg.inv(self.ofc_data.motion_penalty**2 * mat_h + q_mat)

        uk = getattr(self, f"calc_uk_{self.ofc_data.xref}")(
            mat_f=mat_f, qx=qx, mat_h=mat_h
        )

        return uk.ravel()
