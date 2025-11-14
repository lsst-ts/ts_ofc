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

__all__ = ["OICController"]

import logging
import typing

import numpy as np

from .. import BendModeToForce, OFCData, SensitivityMatrix
from . import BaseController


class OICController(BaseController):
    """Optimal Integral Controller (OIC)"""

    def __init__(self, ofc_data: OFCData, log: logging.Logger | None = None) -> None:
        # Initialize base class
        super().__init__(ofc_data, log)

        # Constuct the double zernike sensitivity matrix
        self.dz_sensitivity_matrix = SensitivityMatrix(self.ofc_data)

        self.fwhm_threshold = 0.2
        self.default_gain = 0.7

        self.m1m3_bmf = BendModeToForce("M1M3", self.ofc_data)
        self.m2_bmf = BendModeToForce("M2", self.ofc_data)

    def authority(self) -> np.ndarray[float]:
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

    def calc_uk_x00(
        self, mat_f: np.ndarray[float], qx: np.ndarray[float], mat_h: np.ndarray[float]
    ) -> np.ndarray[float]:
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
        mat_h : `numpy.ndarray`
            Matrix H.

        Returns
        -------
        `numpy.ndarray`
            Calculated uk in the basis of degree of freedom (DOF).
        """
        state_diff = self.dof_state[self.ofc_data.dof_idx] - self.dof_state0[self.ofc_data.dof_idx]
        state_diff = state_diff.reshape(-1, 1)

        _qx = qx + self.ofc_data.motion_penalty**2 * mat_h.dot(state_diff)

        return self.calc_uk_x0(mat_f=mat_f, qx=_qx)

    def calc_uk_x0(
        self,
        mat_f: np.ndarray[float],
        qx: np.ndarray[float],
        **kwargs: dict[str, typing.Any],
    ) -> np.ndarray[float]:
        """Calculate uk by referencing to "x0".

        The offset will only trace the previous one.

        uk = -F' * QX.

        Parameters
        ----------
        mat_f : `numpy.ndarray`
            Matrix F.
        qx : `numpy.ndarray`
            qx array.
        kwargs : `dict[str, typing.Any]`
            Additional keyword arguments. This is mainly added to provide
            similar interaface to other `calc_uk_*` methods.

        Returns
        -------
        uk : `numpy.ndarray`
            Calculated uk in the basis of degree of freedom (DOF).
        """
        return mat_f.dot(qx)

    def calc_uk_0(
        self, mat_f: np.ndarray[float], qx: np.ndarray[float], mat_h: np.ndarray[float]
    ) -> np.ndarray[float]:
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

    def uk(
        self,
        filter_name: str,
        dof_state: np.ndarray[float],
        sensor_names: list[str] | None = None,
    ) -> np.ndarray[float]:
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
        sensor_names : `list` [`string`]
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
        RuntimeError
            If Gaussian Quadrature points and weights are not provided for LSST
            instrument.
        RuntimeError
            If sensor names are not provided for full array mode instruments.
        """
        if self.ofc_data.name != "lsst" and sensor_names is None:
            raise RuntimeError("sensor_names must be provided for full array mode instruments.")

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
        # Calculate the y2 correction.
        # If the instrument is LSST, we will use the Gaussian
        # Quadrature points to evaluate the y2 correction.
        # Otherwise, for full array mode instruments,
        # we will use the sensor positions to retrieve the y2 correction.
        if self.ofc_data.name == "lsst":
            if (
                self.ofc_data.gq_points is None
                or self.ofc_data.gq_weights is None
                or self.ofc_data.gq_y2_correction is None
            ):
                raise RuntimeError("gq_points and gq_weights must be provided for LSST instrument.")

            imqw = [self.ofc_data.gq_weights[sensor] for sensor in range(len(self.ofc_data.gq_weights))]
            field_angles = [
                self.ofc_data.gq_points[sensor] for sensor in range(len(self.ofc_data.gq_weights))
            ]
            y2c = np.array([self.ofc_data.gq_y2_correction[idx] for idx in range(len(imqw))])
        else:
            if sensor_names is None:
                raise RuntimeError("sensor_names must be provided for full array mode instruments.")

            imqw = [self.ofc_data.image_quality_weights[sensor] for sensor in sensor_names]
            field_angles = [self.ofc_data.sample_points[sensor] for sensor in sensor_names]
            y2c = np.array([self.ofc_data.y2_correction[sensor] for sensor in sensor_names])

        # Compute normalized image quality weights
        if np.sum(imqw) == 0:
            raise ValueError("Image quality weights sum is zero. Please check your weights.")

        n_imqw = imqw / np.sum(imqw)

        # Evaluate sensitivity matrix at sensor positions
        sensitivity_matrix = self.dz_sensitivity_matrix.evaluate(field_angles)

        # Select sensitivity matrix only at used degrees of freedom
        sensitivity_matrix = sensitivity_matrix[:, self.ofc_data.zn_idx, :]

        # Select sensitivity matrix only at used degrees of freedom
        sensitivity_matrix = sensitivity_matrix[..., self.ofc_data.dof_idx]

        qx = 0
        q_mat = 0
        for sen_mat, wgt, y2k in zip(sensitivity_matrix, n_imqw, y2c):
            y2k = y2k.reshape(-1, 1)
            qx += wgt * sen_mat.T.dot(cc_mat).dot(sen_mat.dot(_dof_state) + y2k[self.ofc_data.zn_idx])
            q_mat += wgt * sen_mat.T.dot(cc_mat).dot(sen_mat)

        # Calculate the F matrix.
        #
        # F = inv(A.T * C.T * C * A + rho * H).

        authority = self.authority()
        dof_idx = self.ofc_data.dof_idx
        mat_h = np.diag(authority[dof_idx] ** 2)

        mat_f = np.linalg.inv(self.ofc_data.motion_penalty**2 * mat_h + q_mat)

        uk = getattr(self, f"calc_uk_{self.ofc_data.xref}")(mat_f=mat_f, qx=qx, mat_h=mat_h)

        return uk.ravel()

    def control_step(
        self,
        filter_name: str,
        dof_state: np.ndarray[float],
        sensor_names: list[str] | None = None,
    ) -> np.ndarray[float]:
        """Estimate uk in the basis of degree of freedom (DOF) with gain
        compensation.

        Parameters
        ----------
        filter_name : `string`
            Name of the filter.
        dof_state : `numpy.ndarray`
            Optical state in the basis of DOF.
        sensor_names : `list` [`string`] or `None`
            List of sensor names.

        Returns
        -------
        control_effort : `numpy.ndarray`
            Calculated uk in the basis of DOF.

        Raises
        ------
        RuntimeError
            If `sensor_names` is not provided for full array mode instruments.
        """

        if (self.ofc_data.name != "lsst") and (sensor_names is None):
            raise RuntimeError("sensor_names must be provided for full array mode instruments.")

        correction = self.uk(filter_name, dof_state, sensor_names)

        # Initialize the control effort with the proportional term
        if self.kp < 0.0 or self.kp is None:
            self.set_pssn_gain()

        control_effort = self.calculate_pid_step(correction)

        return control_effort

    def set_pssn_gain(self) -> None:
        """Set the gain value based on the PSSN, which comes from the FWHM by
        DM team.

        Raises
        ------
        RuntimeError
            If `pssn_data` is not properly set.
        """

        if (len(self.pssn_data["pssn"]) == 0) or (len(self.pssn_data["sensor_names"]) == 0):
            raise RuntimeError("PSSN data not set. Run `set_fwhm_data` with appropriate data.")

        fwhm_gq = self.effective_fwhm_g4(self.pssn_data["pssn"], self.pssn_data["sensor_names"])

        if fwhm_gq > self.fwhm_threshold:
            self.kp = 1.0
        else:
            self.kp = self.default_gain
