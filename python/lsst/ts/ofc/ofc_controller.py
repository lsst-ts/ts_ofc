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

from . import BendModeToForce, SensitivityMatrix


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

        # Constuct the double zernike sensitivity matrix
        self.dz_sensitivity_matrix = SensitivityMatrix(self.ofc_data)

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

    def effective_fwhm_g4(self, pssn, sensor_names):
        """Calculate the effective FWHM by Gaussian quadrature.

        FWHM: Full width at half maximum.
        FWHM = eta * FWHM_{atm} * sqrt(1/PSSN -1).
        Effective GQFWHM = sum_{i} (w_{i}* FWHM_{i}).

        Parameters
        ----------
        pssn : `numpy.ndarray` or `list`
            Normalized point source sensitivity (PSSN).
        sensor_names : `list` of `string`
            List of sensor names.

        Returns
        -------
        `float`
            Effective FWHM in arcsec by Gaussian quadrature.

        Raises
        ------
        ValueError
            Input values are unphysical.
        ValueError
            Image quality weights sum is zero. Please check your weights.
        """

        # Normalized image quality weight
        imqw = [self.ofc_data.image_quality_weights[sensor] for sensor in sensor_names]

        if np.sum(imqw) == 0:
            raise ValueError(
                "Image quality weights sum is zero. Please check your weights."
            )

        n_imqw = imqw / np.sum(imqw)

        fwhm = self.ETA * self.FWHM_ATM * np.sqrt(1.0 / np.array(pssn) - 1.0)
        fwhm_gq = np.sum(n_imqw * fwhm)

        if np.isnan(fwhm_gq) or np.isinf(fwhm_gq):
            raise ValueError("Input values are unphysical.")

        return fwhm_gq

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

    def uk_gain(
        self,
        filter_name: str,
        dof_state: np.ndarray,
        sensor_names: list[str] | None = None,
    ) -> np.ndarray:
        """Estimate uk in the basis of degree of freedom (DOF) with gain
        compensation.

        Parameters
        ----------
        filter_name : `string`
            Name of the filter.
        dof_state : `numpy.ndarray`
            Optical state in the basis of DOF.
        sensor_names : `list` of `string`
            List of sensor names.

        Returns
        -------
        uk : `numpy.ndarray`
            Calculated uk in the basis of DOF.

        Raises
        ------
        RuntimeError
            If `sensor_names` is not provided for full array mode instruments.
        """

        if (self.ofc_data.name != "lsst") and (sensor_names is None):
            raise RuntimeError(
                "sensor_names must be provided for full array mode instruments."
            )

        return self.gain * self.uk(filter_name, dof_state, sensor_names)

    def uk(
        self,
        filter_name: str,
        dof_state: np.ndarray,
        sensor_names: list[str] | None = None,
    ) -> np.ndarray:
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
        sensor_names : `list` of `string`
            List of sensor names.

        Returns
        -------
        uk : `numpy.ndarray`
            Calculated uk in the basis of DOF.

        Raises
        ------
        RuntimeError
            If `xref` strategy is not valid.
        RuntimeError
            If `sensor_names` is not provided for full array mode instruments.
        ValueError
            If image quality weights sum is zero.
        """
        if self.ofc_data.name != "lsst" and sensor_names is None:
            raise RuntimeError(
                "sensor_names must be provided for full array mode instruments."
            )

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

        cc_mat = np.diag(self.ofc_data.alpha[self.ofc_data.zn_idx])

        # Calculate the Qx.
        #
        # Qx = sum_{wi * A.T * C.T * C * (A * yk + y2k)}.

        _dof_state = dof_state.reshape(-1, 1)

        # Evaluate sensitivity matrix at sensor positions
        # If the instrument is LSST, we will use the Gaussian
        # Quadrature points to evaluate the sensitivity matrix.
        # Otherwise, for full array mode LSST or Comcam,
        # we will use the sensor positions 189 or 9 with weights.
        if self.ofc_data.name == "lsst":
            imqw = [
                self.ofc_data.gq_weights[sensor]
                for sensor in range(len(self.ofc_data.gq_weights))
            ]
            field_angles = [
                self.ofc_data.gq_points[sensor]
                for sensor in range(len(self.ofc_data.gq_weights))
            ]
        else:
            imqw = [
                self.ofc_data.image_quality_weights[sensor] for sensor in sensor_names
            ]
            field_angles = [
                self.ofc_data.sample_points[sensor] for sensor in sensor_names
            ]

        # Compute normalized image quality weights
        if np.sum(imqw) == 0:
            raise ValueError(
                "Image quality weights sum is zero. Please check your weights."
            )

        n_imqw = imqw / np.sum(imqw)

        # Evaluate sensitivity matrix at sensor positions
        sensitivity_matrix = self.dz_sensitivity_matrix.evaluate(field_angles)

        # Select sensitivity matrix only at used degrees of freedom
        sensitivity_matrix = sensitivity_matrix[:, self.ofc_data.zn_idx, :]

        # Select sensitivity matrix only at used degrees of freedom
        sensitivity_matrix = sensitivity_matrix[..., self.ofc_data.dof_idx]

        # Calculate the y2 correction.
        # If the instrument is LSST, we will use the Gaussian
        # Quadrature points to evaluate the y2 correction.
        # Otherwise, for full array mode instruments,
        # we will use the sensor positions to retrieve the y2 correction.
        if self.ofc_data.name == "lsst":
            y2c = np.array(
                [self.ofc_data.gq_y2_correction[idx] for idx in range(len(n_imqw))]
            )
        else:
            y2c = np.array(
                [self.ofc_data.y2_correction[sensor] for sensor in sensor_names]
            )

        qx = 0
        q_mat = 0
        for sen_mat, wgt, y2k in zip(sensitivity_matrix, n_imqw, y2c):
            y2k = y2k.reshape(-1, 1)
            qx += wgt * sen_mat.T.dot(cc_mat).dot(
                sen_mat.dot(_dof_state) + y2k[self.ofc_data.zn_idx]
            )
            q_mat += wgt * sen_mat.T.dot(cc_mat).dot(sen_mat)

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

    def fwhm_to_pssn(self, fwhm):
        """Convert the FWHM data to PSSN.

        Take the array of FWHM values (nominally 1 per CCD) and convert
        it to PSSN (nominally 1 per CCD).

        Parameters
        ----------
        fwhm : `numpy.ndarray[x]`
            An array of FWHM values with sensor information.

        Returns
        -------
        pssn : `numpy.ndarray[y]`
            An array of PSSN values.
        """

        denominator = self.ETA * self.FWHM_ATM
        pssn = 1.0 / ((fwhm / denominator) ** 2 + 1.0)

        return pssn
