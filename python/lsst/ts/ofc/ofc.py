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

from . import BendModeToForce, Correction, OFCController, StateEstimator
from .ofc_data import OFCData
from .utils import CorrectionType


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
    lv_dof : `np.ndarray`
        Last visit degrees of freedom.
    ofc_controller : `OFCController`
        Instance of `OFCController` class.
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

        self.pssn_data = dict(sensor_names=None, pssn=None)

        self.ofc_data = ofc_data

        self.state_estimator = StateEstimator(self.ofc_data)

        self.ofc_controller = OFCController(self.ofc_data)

        self.fwhm_threshold = 0.2

        self.default_gain = 0.7

        # Truncation of degenerate modes after correction calculation
        self.rcond_degeneracy = 1e-3

        # Last visit dof
        self.lv_dof = self.ofc_controller.dof_state.copy()

        self.dof_order = ("m2HexPos", "camHexPos", "M1M3Bend", "M2Bend")

    def calculate_corrections(
        self,
        wfe: np.ndarray,
        sensor_names: list[str],
        filter_name: str,
        gain: float,
        rotation_angle: float,
    ) -> list[Correction]:
        """Calculate the Hexapod, M1M3, and M2 corrections from the FWHM
        and wavefront error.

        Parameters
        ----------
        wfe : `np.ndarray`
            An array of arrays (e.g. 2-d array) with wavefront erros. Each
            element contains an array of wavefront errors (in um) for a
            particular detector/field.
        sensor_names: `list`
            List of sensor names.
        filter_name : `string`
            Name of the filter used in the observations. This must be a valid
            entry in the `ofc_data.intrinsic_zk` and `ofc_data.eff_wavelength`
            dictionaries.
        gain : `float`
            User provided gain. If < 0, calculate gain based on point source
            sensitivity normalized (PSSN).
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

        if len(wfe) != len(sensor_names):
            RuntimeError(
                f"Number of wavefront errors ({len(wfe)}) must be the same as "
                f"number of sensors ({len(sensor_names)})."
            )
        # Set the gain value
        if gain < 0.0:
            self.set_pssn_gain()
        else:
            self.ofc_controller.gain = gain

        optical_state = self.state_estimator.dof_state(
            filter_name, wfe, sensor_names, rotation_angle
        )

        # Calculate the uk based on the control algorithm
        uk = self.ofc_controller.uk_gain(filter_name, optical_state, sensor_names)

        # Assign the value to the last visit DOF
        self.set_last_visit_dof(uk)

        # Aggregate the rotated uk
        self.ofc_controller.aggregate_state(uk, self.ofc_data.dof_idx)

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

        dof = self.ofc_controller.dof_state[dof_idx]

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

        self.lv_dof = np.zeros_like(self.ofc_controller.dof_state0)

    def set_fwhm_data(self, fwhm, sensor_names):
        """Set the list of FWHMSensorData of each CCD of camera.
        Parameters
        ----------
        fwhm : `np.ndarray`
            Array of arrays (e.g. 2-d array) which contains the FWHM data.
            Each element contains an array of fwhm (in arcsec) measurements for
            a  particular sensor.
        sensor_names : `list` of `string`
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
            self.pssn_data["pssn"][s_id] = np.average(
                self.ofc_controller.fwhm_to_pssn(fwhm)
            )

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

        self.ofc_controller.reset_dof_state()
        self.init_lv_dof()

        return self.get_all_corrections()

    def set_pssn_gain(self):
        """Set the gain value based on the PSSN, which comes from the FWHM by
        DM team.

        Raises
        ------
        RuntimeError
            If `pssn_data` is not properly set.
        """

        if self.pssn_data["pssn"] is None or self.pssn_data["sensor_names"] is None:
            raise RuntimeError(
                "PSSN data not set. Run `set_fwhm_data` with appropriate data."
            )

        fwhm_gq = self.ofc_controller.effective_fwhm_g4(
            self.pssn_data["pssn"], self.pssn_data["sensor_names"]
        )

        if fwhm_gq > self.fwhm_threshold:
            self.ofc_controller.gain = 1.0
        else:
            self.ofc_controller.gain = self.default_gain

    def set_last_visit_dof(self, dof) -> None:
        """Set the state (or degree of freedom, DOF) correction from the last
        visit.

        Parameters
        ----------
        dof : `numpy.ndarray`
            Calculated degrees of freedom.
        """

        lv_dof = np.zeros_like(self.ofc_controller.dof_state0)

        lv_dof[self.ofc_data.dof_idx] = dof

        self.lv_dof = lv_dof
