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

__all__ = ["OFC"]

import logging

import numpy as np

from . import BendModeToForce, Correction, StateEstimator
from .controllers import BaseController, OICController, PIDController, ZernikeController
from .ofc_data import OFCData
from .utils import CorrectionType, get_filter_name
from .utils.ofc_data_helpers import get_sensor_names


class OFC:
    """Optical Feedback Control.

    This class provides functionality to convert optical wave front errors
    (WFE) into physical corrections for the optical components; M1M3 (force
    figure), M2 (force figure), and Camera and M2 Hexapods (position).

    Parameters
    ----------
    ofc_data : `OFCData`
        Data container.
    log : `logging.Logger` or `None`, optional
        Optional logging class to be used for logging operations. If `None`
        (default), creates a new logger.

    Attributes
    ----------
    default_gain : `float`
        Default gain, used when setting gain in `set_pssn_gain()` when fwhm is
        above `fwhm_threshold`.
    dof_order : `tuple`
        Order of the degrees of freedom.
    fwhm_threshold : `float`
        Full width half maximum threshold when estimating gain with
        `set_pssn_gain()`.
    log : `logging.Logger`
        Logger class used for logging operations.
    lv_dof : `np.ndarray[float]`
        Last visit degrees of freedom.
    controller : `PIDController` or `OICController`
        Controller class.
    ofc_data : `OFCData`
        OFC data container.
    pssn_data : `dict`
        Normalized point source sensitivity data.
    state_estimator : `StateEstimator`
        Instance of `StateEstimator`.

    Notes
    -----
    FWHM: Full width at half maximum.
    PSSN: Normalized point source sensitivity.
    """

    def __init__(self, ofc_data: OFCData, log: logging.Logger | None = None) -> None:
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        self.ofc_data = ofc_data

        self.state_estimator = StateEstimator(self.ofc_data, log=self.log)

        self.zernike_controller = ZernikeController(
            self.ofc_data, num_sensors=4, log=self.log
        )

        self.set_controller(self.ofc_data.controller["name"])

        # Truncation of degenerate modes after correction calculation
        self.rcond_degeneracy = 1e-3

        # Last visit dof
        self.lv_dof = self.controller.dof_state.copy()

        self.dof_order = ("m2HexPos", "camHexPos", "M1M3Bend", "M2Bend")

    def set_controller(self, controller_name: str) -> None:
        """Set the controller to be used.

        Parameters
        ----------
        controller_name : `str`
            Name of the controller. Options are: "PID", "OIC".
        """
        if controller_name == "PID":
            self.controller: BaseController = PIDController(self.ofc_data)
        elif controller_name == "OIC":
            self.controller = OICController(self.ofc_data)
        else:
            raise ValueError(
                f"Unknown controller name: {controller_name}. "
                f"Options are: 'PID', 'OIC'."
            )

    def set_controller_filename(self, controller_filename: str) -> None:
        """Set the controller filename.

        Parameters
        ----------
        controller_filename : `str`
            Filename of the controller.
        """
        self.ofc_data.controller_filename = controller_filename
        self.set_controller(self.ofc_data.controller["name"])

    def set_truncation_index(self, truncation_index: int) -> None:
        """Set the truncation index for the controller.

        Parameters
        ----------
        truncation_index : `int`
            Truncation index.
        """
        self.ofc_data.controller["truncation_index"] = truncation_index
        self.state_estimator = StateEstimator(self.ofc_data)

    def calculate_corrections(
        self,
        wfe: np.ndarray[float],
        sensor_ids: np.ndarray[int],
        filter_name: str,
        rotation_angle: float,
    ) -> list[Correction]:
        """Calculate the Hexapod, M1M3, and M2 corrections from the FWHM
        and wavefront error.

        Parameters
        ----------
        wfe : `np.ndarray[float]`
            An array of arrays (e.g. 2-d array) with wavefront erros. Each
            element contains an array of wavefront errors (in um) for a
            particular detector/field.
        sensor_ids: np.ndarray[int]
            List of sensor ids.
        filter_name : `string`
            Name of the filter used in the observations.
        rotation_angle : `float`
            Camera rotator angle (in degrees) during the observations.

        Returns
        -------
        corrections : `list` of `Correction`
            Corrections for the individual componets. Order is: M2 Hexapod,
            Camera Hexapod, M1M3 and M2.

        Raises
        ------
        RuntimeError
            If size of `wfe` is different than `sensor_names`.
        """

        if len(wfe) != len(sensor_ids):
            RuntimeError(
                f"Number of wavefront errors ({len(wfe)}) must be the same as "
                f"number of sensors ({len(sensor_ids)})."
            )

        self.log.debug(
            f"Gain {self.controller.kp} "
            f"ofc_data truncation index {self.ofc_data.controller.get('truncation_index', None)} "
            f"state estimator truncation index {self.state_estimator.truncate_index} "
            f"and ofc_data threshold {self.ofc_data.controller.get('truncation_threshold', None)} "
            f"state estimator rcond {self.state_estimator.rcond}"
        )
        # Remove NaN values and corresponding sensor_ids
        valid_indices = ~np.isnan(wfe).any(axis=1)
        wfe = wfe[valid_indices]
        sensor_ids = np.array(sensor_ids)[valid_indices]

        # Process filter name to be in the correct format.
        filter_name = get_filter_name(filter_name)
        # Get sensor names from sensor ids
        sensor_names = get_sensor_names(ofc_data=self.ofc_data, sensor_ids=sensor_ids)

        zernike_step = self.zernike_controller.control_step(
            filter_name,
            wfe,
            sensor_names,
            rotation_angle + self.ofc_data.rotation_offset,
        )

        optical_state = self.state_estimator.dof_state(
            filter_name,
            -zernike_step[:, self.ofc_data.zn_idx],
            sensor_names,
            rotation_angle + self.ofc_data.rotation_offset,
        )

        # Calculate the uk based on the control algorithm
        uk = -self.controller.control_step(filter_name, optical_state, sensor_names)

        # Assign the value to the last visit DOF
        self.set_last_visit_dof(uk)

        # Aggregate the rotated uk
        self.controller.aggregate_state(uk, self.ofc_data.dof_idx)

        return self.get_all_corrections()

    def get_all_corrections(self) -> list[Correction]:
        """Return corrections for all components in the appropriate order.

        Returns
        -------
        corrections : `list` of `Corrections`
        """

        corrections = [self.get_correction(comp) for comp in self.dof_order]

        return corrections

    def get_correction(self, dof_comp: str) -> Correction:
        """Get the aggregated correction for specified component.

        DOF: Degree of freedom.

        Parameters
        ----------
        dof_comp : `string`
            Name of the component in the DOF index dictionary. See
            `OFData.comp_dof_idx`.

        Returns
        -------
        correction : `Correction`
            Component correction.
        """

        start_idx = self.ofc_data.comp_dof_idx[dof_comp]["startIdx"]
        end_idx = start_idx + self.ofc_data.comp_dof_idx[dof_comp]["idxLength"]
        dof_idx = np.arange(start_idx, end_idx)

        dof = self.controller.dof_state[dof_idx]

        if isinstance(self.ofc_data.comp_dof_idx[dof_comp]["rot_mat"], float):
            trans_dof = self.ofc_data.comp_dof_idx[dof_comp]["rot_mat"] * dof
        else:
            inv_rot_mat = np.linalg.pinv(
                self.ofc_data.comp_dof_idx[dof_comp]["rot_mat"]
            )

            trans_dof = inv_rot_mat.dot(dof.reshape(-1, 1)).ravel()

        correction = Correction(*trans_dof)

        if correction.correction_type != CorrectionType.POSITION:
            bm2f = BendModeToForce(component=dof_comp[:-4], ofc_data=self.ofc_data)
            correction = Correction(*bm2f.force(trans_dof))

        return correction

    def init_lv_dof(self) -> None:
        """Initialize last visit degree of freedom."""

        self.lv_dof = np.zeros_like(self.controller.dof_state0)

    def set_fwhm_data(
        self, fwhm: np.ndarray[float], sensor_ids: np.ndarray[int]
    ) -> None:
        """Set the list of FWHMSensorData of each CCD of camera.
        Parameters
        ----------
        fwhm : `np.ndarray[float]`
            Array of arrays (e.g. 2-d array) which contains the FWHM data.
            Each element contains an array of fwhm (in arcsec) measurements for
            a  particular sensor.
        sensor_ids : `np.ndarray[int]`
            List of sensor ids.
        """

        # Get sensor names from sensor ids
        sensor_names = get_sensor_names(ofc_data=self.ofc_data, sensor_ids=sensor_ids)

        # Delegate the call to the controller's set_fwhm_data
        self.controller.set_fwhm_data(fwhm, sensor_names)

    def reset(self) -> list[Correction]:
        """Reset the OFC calculation state, which is the aggregated DOF now.

        This function is needed for the long slew angle of telescope.

        DOF: Degree of freedom.

        Returns
        -------
        M2HexapodCorrection
            The position offset for the MT M2 Hexapod.
        CameraHexapodCorrection
            The position offset for the MT Hexapod.
        M1M3Correction
            The figure offset for the MT M1M3.
        M2Correction
            The figure offset for the MT M2.
        """

        self.controller.reset_dof_state()
        self.init_lv_dof()

        return self.get_all_corrections()

    def set_last_visit_dof(self, dof: np.ndarray[float]) -> None:
        """Set the state (or degree of freedom, DOF) correction from the last
        visit.

        Parameters
        ----------
        dof : `numpy.ndarray`
            Calculated degrees of freedom.
        """

        lv_dof = np.zeros_like(self.controller.dof_state0)

        lv_dof[self.ofc_data.dof_idx] = dof

        self.lv_dof = lv_dof
