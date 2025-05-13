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

import galsim
import numpy as np

from .. import OFCData
from ..utils.ofc_data_helpers import get_intrinsic_zernikes

__all__ = ["ZernikeController"]


class ZernikeController:
    """Zernike Controller.

    This class is mainly used to determine the zernike step (`zk`)
    at time `k+1` based on the wavefront error (`yk`) at time
    `k`.

    Parameters
    ----------
    ofc_data : `OFCData`
        OFC Data.
    log : `logging.Logger` or `None`
        Optional logging class to be used for logging operations. If `None`,
        creates a new logger.

    Attributes
    ----------
    zk_state : `np.array`
        State of telescope in the basis of degrees of freedom.
    zk_state0 : `np.array`
        Initial state of telescope in the basis of degrees of freedom.
    integral : `np.array`
        Integral of the error.
    kp : `float`
        Proportional gain.
    ki : `float`
        Integral gain.
    kd : `float`
        Derivative gain.
    log : `logging.Logger`
        Logger class used for logging operations.
    ofc_data : `OFCData`
        OFC data.
    previous_error : `np.array`
        Previous error.
    pssn_data : `dict`
        PSSN data.
    setpoint : `np.array`
        Setpoint for the PID controller.
    """

    # Eta in FWHM calculation.
    ETA = 1.086

    # FWHM in atmosphere.
    FWHM_ATM = 0.6

    def __init__(
        self, ofc_data: OFCData, num_sensors: int = 4, log: logging.Logger | None = None
    ) -> None:
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        # Set OFC data
        self.ofc_data = ofc_data

        # Set gains and setpoint
        self._kp = self.ofc_data.zk_controller["kp"]
        self._ki = self.ofc_data.zk_controller["ki"]
        self._kd = self.ofc_data.zk_controller["kd"]
        self._derivative_filter_coeff = self.ofc_data.zk_controller[
            "derivative_filter_coeff"
        ]
        self.setpoint = np.array(self.ofc_data.zk_controller["setpoint"])

        # Set initial state
        num_zk = self.ofc_data.znmax - self.ofc_data.znmin + 1
        self.zk_state0 = np.zeros((num_sensors, num_zk))
        self.zk_state = self.zk_state0.copy()

        # Initialize previous error and integral
        self.previous_error = self.setpoint - self.zk_state0
        self._integral = self.previous_error
        self.filtered_derivative = np.zeros((num_sensors, num_zk))

    @property
    def kp(self) -> float:
        return self._kp

    @kp.setter
    def kp(self, value: float) -> None:
        self._kp = value

    @property
    def ki(self) -> float:
        return self._ki

    @ki.setter
    def ki(self, value: float) -> None:
        self._ki = value

    @property
    def kd(self) -> float:
        return self._kd

    @kd.setter
    def kd(self, value: float) -> None:
        self._kd = value

    @property
    def derivative_filter_coeff(self) -> float:
        return self._derivative_filter_coeff

    @derivative_filter_coeff.setter
    def derivative_filter_coeff(self, value: float) -> None:
        self._derivative_filter_coeff = value

    def reset_zk_state(self) -> None:
        """Initialize the state to the state 0 in the basis of degree of
        freedom (DOF).
        """
        self.zk_state = self.zk_state0.copy()

    def aggregate_state(
        self, zk: np.ndarray[float] | list, zn_idx: np.ndarray[int] | list[int]
    ) -> None:
        """Aggregate the calculated degree of freedom (zk) in the state.

        Parameters
        ----------
        zk : `numpy.ndarray` or `list`
            Calculated zks.
        zn_idx : `numpy.ndarray` or `list[int]`
            Index array of degree of freedom.
        """
        self.zk_state += zk

    @property
    def aggregated_state(self) -> np.ndarray[float]:
        """Returns the aggregated state.

        Returns
        -------
        `np.ndarray[float]`
            Aggregated state.
        """
        return self.zk_state

    def set_aggregated_state(self, value: np.ndarray[float]) -> None:
        """Set the aggregated state.

        Parameters
        ----------
        value : `np.ndarray[float]`
            Aggregated state.
        """
        self.zk_state += value

    def reset_history(self) -> None:
        """Reset the history of the controller."""
        self.zk_state0 = self.zk_state.copy()
        self.integral = self.setpoint - self.zk_state
        self.previous_error = self.integral.copy()
        self.filtered_derivative = np.zeros_like(self.zk_state)

    def control_step(
        self,
        filter_name: str,
        wfe: np.ndarray[float],
        sensor_names: list[str],
        rotation_angle: float = 0.0,
    ) -> np.ndarray[float]:
        """Estimate uk in the basis of degree of freedom (DOF).

        Parameters
        ----------
        filter_name : `string`
            Name of the filter.
        zk_state : `numpy.ndarray`
            Optical state in the basis of DOF.
        sensor_names : `list` [`string`]
            List of sensor names.
        rotation_angle : `float`
            Rotation angle in degrees.

        Raises
        ------
        NotImplementedError
            Child class should implemented this.
        """
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
            wfe[idx, :] = zk_galsim.rotate(np.deg2rad(rotation_angle)).coef[
                self.ofc_data.znmin :
            ]

        self.log.debug(f"Derotated wavefront error: {wfe}")
        # Compute wavefront error deviation from the intrinsic wavefront error
        # y = wfe - intrinsic_zk - y2_correction
        # y2_correction is a static correction for the
        # deviation currently set to zero.
        y2_correction = np.array(
            [self.ofc_data.y2_correction[sensor] for sensor in sensor_names]
        )
        y = (
            wfe
            - get_intrinsic_zernikes(
                self.ofc_data, filter_name, sensor_names, rotation_angle
            )
            - y2_correction
        )
        conversion_factors = self.getPsfGradPerZernike(jmax=28)

        zernike_step = self.calculate_pid_step(y * conversion_factors[np.newaxis, :])

        return zernike_step / conversion_factors[np.newaxis, :]

    def calculate_pid_step(self, state: np.ndarray[float]) -> np.ndarray[float]:
        """
        Calculate the control signal using PID controller.

        Parameters
        ----------
        state : `np.ndarray[float]`
            State of the system.

        Returns
        -------
        uk : `numpy.ndarray`
            Calculated uk in the basis of DOF.
        """
        error = self.setpoint - state
        self.integral = error
        self.integral = np.clip(
            self.integral,
            -self.ofc_data.max_zk_integral,
            self.ofc_data.max_zk_integral,
        )
        derivative = error - self.previous_error

        # Apply low-pass filter to the derivative term
        self.filtered_derivative = (
            self.derivative_filter_coeff * derivative
            + (1 - self.derivative_filter_coeff) * self.filtered_derivative
        )

        uk = (
            self.kp * error
            + self.ki * self.integral
            + self.kd * self.filtered_derivative
        )
        self.previous_error = error
        return uk

    def getPsfGradPerZernike(
        self,
        diameter: float = 8.36,
        obscuration: float = 0.612,
        jmin: int = 4,
        jmax: int = 22,
    ) -> np.ndarray:
        """Get the gradient of the PSF FWHM with respect to each Zernike.

        This function takes no positional arguments. All parameters must be
        by name (see the list of parameters below).

        Parameters
        ----------
        diameter : float, optional
            The diameter of the telescope aperture, in meters.
            (the default, 8.36, corresponds to the LSST primary mirror)
        obscuration : float, optional
            Central obscuration of telescope aperture (i.e. R_outer / R_inner).
            (the default, 0.612, corresponds to the LSST primary mirror)
        jmin : int, optional
            The minimum Noll index, inclusive. Must be >= 0. (the default is 4)
        jmax : int, optional
            The max Zernike Noll index, inclusive. Must be >= jmin.
            (the default is 22.)

        Returns
        -------
        np.ndarray
            Gradient of the PSF FWHM with respect to the corresponding Zernike.
            Units are arcsec / micron.

        Raises
        ------
        ValueError
            If jmin is negative or jmax is less than jmin
        """
        # Check jmin and jmax
        if jmin < 0:
            raise ValueError("jmin cannot be negative.")
        if jmax < jmin:
            raise ValueError("jmax must be greater than jmin.")

        # Calculate the conversion factors
        conversion_factors = np.zeros(jmax + 1)
        for i in range(jmin, jmax + 1):
            # Set coefficients for this Noll index: coefs = [0, 0, ..., 1]
            # Note the first coefficient is Noll index 0, which does not exist
            # is therefore always ignored by galsim
            coefs = [0] * i + [1]

            # Create the Zernike polynomial with these coefficients
            R_outer = diameter / 2
            R_inner = R_outer * obscuration
            Z = galsim.zernike.Zernike(coefs, R_outer=R_outer, R_inner=R_inner)

            # We can calculate the size of the PSF from the RMS of the gradient
            # the wavefront. The gradient of the wavefront perturbs photon path
            # The RMS quantifies the size of the collective perturbation.
            # If we expand the wavefront gradient in another series of Zernike
            # polynomials, we can exploit the orthonormality of the Zernikes to
            # calculate the RMS from the Zernike coefficients.
            rms_tilt = np.sqrt(np.sum(Z.gradX.coef**2 + Z.gradY.coef**2) / 2)

            # Convert to arcsec per micron
            rms_tilt = np.rad2deg(rms_tilt * 1e-6) * 3600

            # Convert rms -> fwhm
            fwhm_tilt = 2 * np.sqrt(2 * np.log(2)) * rms_tilt

            # Save this conversion factor
            conversion_factors[i] = fwhm_tilt

        return conversion_factors[jmin:]
