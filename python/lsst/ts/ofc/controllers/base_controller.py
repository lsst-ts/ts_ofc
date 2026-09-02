# This file is part of ts_ofc.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import logging
from collections import deque

import numpy as np

from .. import OFCData

__all__ = ["BaseController"]


# TODO: DM-45103 Add saturator once bending mode limits are determined.
class BaseController:
    """Base Controller.

    This class is the base class for all the controllers.
    This class is mainly used to determine the offset (`uk`) of degree of
    freedom (DOF) at time `k+1` based on the wavefront error (`yk`) at time
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
    dof_state : `np.array`
        State of telescope in the basis of degrees of freedom.
    dof_state0 : `np.array`
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
    previous_error : `collections.deque`
        List of previous errors.
    pssn_data : `dict`
        PSSN data.
    setpoint : `np.array`
        Setpoint for the PID controller.
    use_leaky_integrator : `bool`
        Whether to use the leaky integrator for the integral term.
    """

    # Eta in FWHM calculation.
    ETA = 1.086

    # FWHM in atmosphere.
    FWHM_ATM = 0.6

    def __init__(self, ofc_data: OFCData, log: logging.Logger | None = None) -> None:
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        # Set OFC data
        self.ofc_data = ofc_data

        # Set gains and setpoint
        self._kp = self.format_gain_array(self.ofc_data.controller["kp"], label="kp")
        self._ki = self.format_gain_array(self.ofc_data.controller["ki"], label="ki")
        self._kd = self.format_gain_array(self.ofc_data.controller["kd"], label="kd")
        self._derivative_filter_coeff = self.ofc_data.controller["derivative_filter_coeff"]
        self.setpoint = np.array(self.ofc_data.controller["setpoint"])
        self._n_iterms = self.ofc_data.n_iterms
        self._i_factor = self.ofc_data.i_factor
        self.use_leaky_integrator = self.ofc_data.use_leaky_integrator

        # Set initial state
        self.dof_state0 = np.zeros(len(self.ofc_data.dof_idx))

        for comp in self.ofc_data.comp_dof_idx:
            start_idx = self.ofc_data.comp_dof_idx[comp]["startIdx"]
            end_idx = (
                self.ofc_data.comp_dof_idx[comp]["startIdx"] + self.ofc_data.comp_dof_idx[comp]["idxLength"]
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
                        self.ofc_data.dof_state0[state0name][f"mode{mode_idx + 1}"]
                        for mode_idx in range(self.ofc_data.comp_dof_idx[comp]["idxLength"])
                    ]
                )

        self.dof_state = self.dof_state0.copy()

        # Initialize previous error and integral
        # Leaky integral weights can just be calculated once
        # at the beginning
        self.previous_error: deque[np.ndarray] = deque(maxlen=self._n_iterms)
        self._set_integral_weights()
        self.integral = np.zeros(len(self.ofc_data.dof_idx))
        self.filtered_derivative = np.zeros(len(self.ofc_data.dof_idx))

        # Initialize PSSN data
        self.pssn_data: dict = dict(sensor_names=[], pssn=[])

    def format_gain_array(self, value: float | np.ndarray[float], label: str = "") -> np.ndarray[float]:
        """Set gain array.

        Parameters
        ----------
        value : `float` or `numpy.ndarray`
            Gain value.
        label : `str`, optional
            Label for logging purposes.

        Returns
        -------
        gain_array : `numpy.ndarray`
            Gain array.

        Raises
        ------
        ValueError
            If length of gain array does not match number of DOFs.
        """
        if isinstance(value, np.ndarray):
            if len(value) != self.ofc_data.ndofs:
                raise ValueError(
                    f"Length of {label or 'gain'} array ({len(value)}) "
                    f"does not match number of DOFs ({self.ofc_data.ndofs})."
                )
            return value
        else:
            return np.full(self.ofc_data.ndofs, value)

    @property
    def kp(self) -> np.ndarray[float]:
        """Proportional gain."""
        return self._kp

    @kp.setter
    def kp(self, value: float | np.ndarray[float]) -> None:
        """Set proportional gain.

        Parameters
        ----------
        value : `float` or `numpy.ndarray`
            Proportional gain.
        """
        self._kp = self.format_gain_array(value, label="kp")

    @property
    def ki(self) -> np.ndarray[float]:
        """Integral gain.

        Returns
        -------
        `np.ndarray[float]`
            Integral gain.
        """
        return self._ki

    @ki.setter
    def ki(self, value: float | np.ndarray[float]) -> None:
        """Set integral gain.

        Parameters
        ----------
        value : `float` or `numpy.ndarray`
            Integral gain.
        """
        self._ki = self.format_gain_array(value, label="ki")

    @property
    def kd(self) -> np.ndarray[float]:
        """Derivative gain.

        Returns
        -------
        `np.ndarray[float]`
            Derivative gain.
        """
        return self._kd

    @kd.setter
    def kd(self, value: float | np.ndarray[float]) -> None:
        """Set derivative gain.

        Parameters
        ----------
        value : `float` or `numpy.ndarray`
            Derivative gain.
        """
        self._kd = self.format_gain_array(value, label="kd")

    @property
    def derivative_filter_coeff(self) -> float:
        """Derivative filter coefficient.

        Returns
        -------
        `float`
            Derivative filter coefficient.
        """
        return self._derivative_filter_coeff

    @derivative_filter_coeff.setter
    def derivative_filter_coeff(self, value: float) -> None:
        self._derivative_filter_coeff = value

    def reset_dof_state(self) -> None:
        """Initialize the state to the state 0 in the basis of degree of
        freedom (DOF).
        """
        self.dof_state = self.dof_state0.copy()

    def aggregate_state(self, dof: np.ndarray[float] | list, dof_idx: np.ndarray[int] | list[int]) -> None:
        """Aggregate the calculated degree of freedom (DOF) in the state.

        Parameters
        ----------
        dof : `numpy.ndarray` or `list`
            Calculated DOF.
        dof_idx : `numpy.ndarray` or `list[int]`
            Index array of degree of freedom.
        """
        self.dof_state[dof_idx] += dof

    @property
    def aggregated_state(self) -> np.ndarray[float]:
        """Returns the aggregated state in the basis of dofs.

        Returns
        -------
        `np.ndarray[float]`
            Aggregated state.
        """
        return self.dof_state

    def set_aggregated_state(self, value: np.ndarray[float]) -> None:
        """Set the aggregated state in the basis of dofs.

        Parameters
        ----------
        value : `np.ndarray[float]`
            Aggregated state.
        """
        self.dof_state[self.ofc_data.dof_idx] = value

    def _set_integral_weights(self) -> None:
        """Set leaky integral weights for the active DOFs.

        The weights array has one row per retained error sample and one column
        per active DOF. Older errors receive exponentially smaller weights,
        while the newest error has weight 1.
        """
        self.integral_weights: np.ndarray = np.array(
            [(self._i_factor**i) * np.ones(len(self.ofc_data.dof_idx)) for i in range(self._n_iterms)]
        )
        # Flip the order so that the newest error is last
        self.integral_weights = self.integral_weights[::-1]

    def reset_history(self) -> None:
        """Reset the history of the controller."""
        self.dof_state0 = self.dof_state.copy()
        self.integral = np.zeros(len(self.ofc_data.dof_idx))
        self.previous_error = deque(maxlen=self._n_iterms)
        self._set_integral_weights()
        self.filtered_derivative = np.zeros(len(self.ofc_data.dof_idx))

    def control_step(
        self,
        filter_name: str,
        dof_state: np.ndarray[float],
        sensor_names: list[str] | None = None,
        control_vmodes: bool = False,
    ) -> np.ndarray[float]:
        """Estimate uk in the basis of degree of freedom (DOF).

        Parameters
        ----------
        filter_name : `string`
            Name of the filter.
        dof_state : `numpy.ndarray`
            Optical state in the basis of DOF.
        sensor_names : `list` [`string`]
            List of sensor names.
        control_vmodes : `bool`, optional
            Whether to control in v-modes space. Default is `False`.

        Raises
        ------
        NotImplementedError
            Child class should implemented this.
        """
        raise NotImplementedError("Child class should implement this.")

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
            Calculated uk in the basis of the state provided,
            either dofs or v-modes.
        """
        error = self.setpoint[self.ofc_data.dof_idx] - state
        pid_log_message = f"Error before any gains in whichever basis PID is {error}.\n"
        previous_error = (
            self.previous_error[-1] if len(self.previous_error) > 0 else np.zeros(len(self.ofc_data.dof_idx))
        )
        derivative = error - previous_error
        self.previous_error.append(error)

        if self.use_leaky_integrator:
            if self.integral_weights.shape[1] != len(self.ofc_data.dof_idx):
                self.integral_weights = self.integral_weights[:, self.ofc_data.dof_idx]
            self.integral = np.sum(
                self.integral_weights[-len(self.previous_error) :] * np.array(self.previous_error),
                axis=0,
            )
        else:
            self.integral += error
        pid_log_message += f"Integral component before clipping is {self.integral}.\n"
        self.integral = np.clip(
            self.integral,
            -self.ofc_data.max_integral[self.ofc_data.dof_idx],
            self.ofc_data.max_integral[self.ofc_data.dof_idx],
        )
        pid_log_message += f"Integral component is {self.integral}.\n"

        # Apply low-pass filter to the derivative term
        self.filtered_derivative = (
            self.derivative_filter_coeff * derivative
            + (1 - self.derivative_filter_coeff) * self.filtered_derivative
        )
        uk = (
            self.kp[self.ofc_data.dof_idx] * error
            + self.ki[self.ofc_data.dof_idx] * self.integral
            + self.kd[self.ofc_data.dof_idx] * self.filtered_derivative
        )
        pid_log_message += f"Corrections after Kp/Ki/Kd gains is {uk}."
        self.log.info(pid_log_message)

        return uk

    def effective_fwhm_g4(self, pssn: np.ndarray[float], sensor_names: list[str]) -> float:
        """Calculate the effective FWHM by Gaussian quadrature.

        FWHM: Full width at half maximum.
        FWHM = eta * FWHM_{atm} * sqrt(1/PSSN -1).
        Effective GQFWHM = sum_{i} (w_{i}* FWHM_{i}).

        Parameters
        ----------
        pssn : `numpy.ndarray` or `list`
            Normalized point source sensitivity (PSSN).
        sensor_names : `list` [`string`]
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
            raise ValueError("Image quality weights sum is zero. Please check your weights.")

        n_imqw = imqw / np.sum(imqw)

        fwhm = self.ETA * self.FWHM_ATM * np.sqrt(1.0 / np.array(pssn) - 1.0)
        fwhm_gq = np.sum(n_imqw * fwhm)

        if np.isnan(fwhm_gq) or np.isinf(fwhm_gq):
            raise ValueError("Input values are unphysical.")

        return fwhm_gq

    def fwhm_to_pssn(self, fwhm: np.ndarray[float]) -> np.ndarray[float]:
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

    def set_fwhm_data(self, fwhm: np.ndarray[float], sensor_names: list[str]) -> None:
        """Set the list of FWHMSensorData of each CCD of camera.
        Parameters
        ----------
        fwhm : `np.ndarray[float]`
            Array of arrays (e.g. 2-d array) which contains the FWHM data.
            Each element contains an array of fwhm (in arcsec) measurements for
            a  particular sensor.
        sensor_names : `list` [`string`]
            List of sensor names.
        Raises
        ------
        RuntimeError
            If size of `fwhm` and `sensor_names` are different.
        """

        if len(fwhm) != len(sensor_names):
            raise RuntimeError(
                f"Size of fwhm ({len(fwhm)}) is different than sensor_names ({len(sensor_names)})."
            )

        self.pssn_data["sensor_names"] = sensor_names.copy()
        self.pssn_data["pssn"] = np.zeros(len(fwhm))

        for s_id, fw in enumerate(fwhm):
            self.pssn_data["pssn"][s_id] = np.average(self.fwhm_to_pssn(fwhm))
