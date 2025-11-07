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

__all__ = ["BendModeToForce"]

import numpy as np

from .ofc_data import OFCData
from .utils import rot_1d_array


class BendModeToForce:
    """Bending mode class to compute actuator forces and mirror stresses
    from bending modes and retrieve bending modes from actuator forces.

    Parameters
    ----------
    component : `string`
        Name of the component. Must be in the `ofc_data.bend_mode` dictionary.
    ofc_data : `OFCData`
        Data container class.

    Attributes
    ----------
    component : `string`
        Name of the component in the `ofc_data.bend_mode` dictionary.
    ofc_data : `OFCData`
        OFC data container class.
    RCOND : `float`
        Cutoff for small singular values, used when computing pseudo-inverse
        matrix.
    bending_mode_stresses_positive : `np.ndarray[float]`
        Bending mode stresses in psi/um for tensile stress.
    bending_mode_stresses_negative : `np.ndarray[float]`
        Bending mode stresses in psi/um for compressive stress.
    rot_mat : `np.ndarray[float]`
        Influence matrix relating bending mode to actuator force.

    Raises
    ------
    RuntimeError
        If the `component` attribute string is not a valid entry in the
        `ofc_data.bend_mode` dictionary.
        If the component name does not map into a valid entry in the
        `ofc_data.comp_dof_idx` dictionary.
    """

    RCOND = 1e-4

    def __init__(self, component: str, ofc_data: OFCData) -> None:
        self.component = component

        self.ofc_data = ofc_data

        if component not in self.ofc_data.bend_mode:
            raise RuntimeError(
                f"Component {component} not in the bend mode list. "
                f"Must be one of {self.ofc_data.bend_mode.keys()}"
            )

        # Load the bending mode stresses data
        self.bending_mode_stresses_positive = np.array(
            self.ofc_data.bending_mode_stresses[self.component]["bending_mode_stress_positive"]
        )
        self.bending_mode_stresses_negative = np.array(
            self.ofc_data.bending_mode_stresses[self.component]["bending_mode_stress_negative"]
        )

        dof_idx_name = f"{component}Bend"

        if dof_idx_name not in self.ofc_data.comp_dof_idx:
            bend_comp = [comp[:-4] for comp in self.ofc_data.comp_dof_idx if comp.endswith("Bend")]
            raise RuntimeError(
                f"Component {component} not a bend mode component. Must be one of {bend_comp}."
            )
        n_bending_modes = self.ofc_data.comp_dof_idx[dof_idx_name]["idxLength"]

        # Influence matrix to rotate the basis from bending mode to actuator
        # forces
        # The first three terms (actuator ID in ZEMAX, x position in m,
        # y position in m) are not needed.
        usecols = np.arange(3, 3 + n_bending_modes)

        self.rot_mat = np.array(self.ofc_data.bend_mode[component]["force"]["data"])[:, usecols]

    def get_stresses_from_dof(self, dof: np.ndarray[float]) -> np.ndarray[float]:
        """Calculated mirror stress in psi per bending mode of the mirror.

        Parameters
        ----------
        dof : `numpy.ndarray`
            Mirror bending mode DOF in um.

        Returns
        -------
        `np.ndarray`
            Mirror stress in psi per bending mode.
        """
        # Apply the positive (tensile) or negative (compressive)
        # bending mode stresses based on the sign of the DOF
        stresses = np.where(
            dof >= 0,
            dof * self.bending_mode_stresses_positive,  # Use positive stress values for positive DOF
            dof * self.bending_mode_stresses_negative,
        )  # Use negative stress values for negative DOF

        return stresses

    def force(self, dof: np.ndarray[float]) -> np.ndarray[float]:
        """Calculate the actuator forces in N based on the degree of freedom
        (DOF).

        Parameters
        ----------
        dof : `numpy.ndarray`
            Mirror DOF in um.

        Returns
        -------
        `numpy.ndarray`
            Actuator forces in N.
        """

        return rot_1d_array(dof, self.rot_mat)

    def bending_mode(self, force: np.ndarray[float]) -> np.ndarray[float]:
        """Compute the bending mode.

        Parameters
        ----------
        force : `numpy.ndarray`
            Actuator forces in N.

        Returns
        -------
        `numpy.ndarray`
            Estimated bending mode in um.
        """

        pinv_rot_mat = np.linalg.pinv(self.rot_mat, rcond=self.RCOND)

        return rot_1d_array(force, pinv_rot_mat)
