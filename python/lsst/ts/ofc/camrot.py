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

__all__ = ["CamRot"]

import numpy as np
from scipy.linalg import block_diag


class CamRot:
    """Handle camera rotation.

    Attributes
    ----------
    rot : `float`
        Camera rotator angle in degrees.
    """

    def __init__(self):
        self.rot = 0.0

    def rot_comp_dof(self, component, dof_state, tilt_xy=(0, 0)):
        """Rotate the degree of freedom of specific group.

        Parameters
        ----------
        component : `string`
            Name of the component in the `OFCDate.comp_dof_idx` dictionary
            (see Notes sections for more information).
        dof_state : `numpy.ndarray`
            State in degree of freedom (DOF).
        tilt_xy : `tuple`, optional
            Tilt angle in arcsec. This is the delta value of M2 hexapod
            compared with camera hexapod (M2-camera). Default value is
            (0., 0.).

        Returns
        -------
        rot_dof_state : `numpy.ndarray`
            Rotated DOF state.

        Raises
        ------
        RuntimeError
            If the input parameter string `component` does not contain the
            substring "HexPos" or "Bend".

        Notes
        -----

        The component parameter must express whether the input rotation is for
        a hexapod type component (e.g. position based) or bend mode component.
        Hexapods must have "HexPos" appended to their name whereas bend mode
        components must have "Bend".

        For exemple, the following will cause the input data to be processed as
        hexapod:

            >> cam_rot.rot_comp_dof("m2HexPos", ...)
            >> cam_rot.rot_comp_dof("camHexPos", ...)

        and the following as bend mode:

            >> cam_rot.rot_comp_dof("M1M3Bend", ...)
            >> cam_rot.rot_comp_dof("M2Bend", ...)
        """

        # 1 arcsec = 1/3600 deg
        tilt_xy_deg = tuple(tilt / 3600.0 for tilt in tilt_xy)

        if "HexPos" in component and "Bend" in component:
            raise RuntimeError(
                f"Unrecognized component {component}. Must only have substring 'HexPos' or 'Bend', not both."
            )
        if "HexPos" in component:
            rot_dof_state = self.rot_hex_pos(component, dof_state, tilt_xy_deg)
        elif "Bend" in component:
            rot_dof_state = self.rot_bending_mode(component, dof_state, tilt_xy_deg)
        else:
            raise RuntimeError(f"Unrecognized component {component}.")

        return rot_dof_state

    def rot_hex_pos(self, component, hex_pos, tilt_xy):
        """Rotate the hexapod position (degree of freedom, DOF) based on the
        rotation angle.

        Parameters
        ----------
        component : `string`
            Name of the component in the `OFCDate.comp_dof_idx` dictionary.
        hex_pos : `numpy.ndarray`
            Hexapod position: (z, x, y, rx, ry). x, y, and z are in um. rx and
            ry are in arcsec.
        tilt_xy : `tuple`
            Tilt angle in degree. This is the delta value of M2 hexapod
            compared with camera hexapod (M2-camera).

        Returns
        -------
        rot_hex_pos : `numpy.ndarray`
            Rotated hexapod position.
        """

        rot = self.map_rot_tilt_xy(self.rot, tilt_xy)

        rot_mat = self.get_hex_rot_mat(rot)

        rot_hex_pos = rot_mat.dot(np.array(hex_pos).reshape(-1, 1))

        return rot_hex_pos.ravel()

    def map_rot_tilt_xy(self, rot, tilt_xy):
        """Map the rotation angle by tilt x, y axis.

        The input rotation angle (theta') is defined on x', y'-plane, which is
        tilted from x, y-plane. The output rotation angle (theta) is defined
        on x, y-plane. The tilt angles in inputs are defined as tilt x'-x and
        tilt y'-y.

        Parameters
        ----------
        rot : `float`
            Rotation angle in degree.
        tilt_xy : `tuple`
            Tilt angle (x, y) in degree.

        Returns
        -------
        mapped_rot : `float`
            Mapped rotation angle in degree.
        """

        # theta = atan(  tan(theta') * (1 - tilt-x + tilt-y) )
        rot_rad = np.deg2rad(rot)
        tilt_x_rad = np.deg2rad(tilt_xy[0])
        tilt_y_rad = np.deg2rad(tilt_xy[1])

        mapped_rot = np.rad2deg(
            np.arctan(np.tan(rot_rad) * (1 - tilt_x_rad + tilt_y_rad))
        )

        return mapped_rot

    def get_hex_rot_mat(self, rot):
        """Get the hexapod rotation matrix.

        Parameters
        ----------
        rot : `float`
            Rotation angle in degree.

        Returns
        -------
        `numpy.ndarray`
            Hexapod rotation matrix.
        """

        rot_mat = self.rot_mat(rot)

        return block_diag(1, rot_mat, rot_mat)

    def rot_bending_mode(self, component, bending_mode, tilt_xy):
        """Rotate the bending mode (degree of freedom, DOF) based on the
        rotation angle and tilt angle compared with the camera.

        Parameters
        ----------
        component : `string`
            DOF group.
        bending_mode : `numpy.ndarray`
            20 mirror bending mode.
        tilt_xy : `tuple`
            Tilt angle in degree. This is the delta value of M2 hexapod
            compared with camera hexapod (M2-camera).

        Returns
        -------
        rot_bending_mode : `numpy.ndarray`
            Rotated bending mode.
        """

        rot = self.map_rot_tilt_xy(self.rot, tilt_xy)
        rot_mat = self.get_mirror_rot_mat(component, rot)
        rot_bending_mode = rot_mat.dot(bending_mode.reshape(-1, 1))

        return rot_bending_mode.ravel()

    def get_mirror_rot_mat(self, component, rot):
        """Get the mirror rotation matrix.

        Parameters
        ----------
        component : `string`
            DOF group.
        rot : `float`
            Rotation angle in degree.

        Returns
        -------
        `numpy.ndarray`
            Mirror rotation matrix.

        Raises
        ------
        RuntimeError
            If component name is not a valid input; M1M3Bend or M2Bend.
        """

        rot_mat = self.rot_mat(rot)

        if component == "M1M3Bend":
            return block_diag(
                rot_mat,
                1,
                rot_mat,
                rot_mat,
                rot_mat,
                rot_mat,
                1,
                rot_mat,
                rot_mat,
                rot_mat,
                1,
                1,
            )
        elif component == "M2Bend":
            return block_diag(
                rot_mat,
                rot_mat,
                1,
                rot_mat,
                rot_mat,
                rot_mat,
                rot_mat,
                rot_mat,
                rot_mat,
                rot_mat,
                1,
            )
        else:
            raise RuntimeError(
                f"Unrecognized component {component}. Must be either M1M3Bend or M2Bend."
            )

    @staticmethod
    def rot_mat(rot):
        """Return rotation matrix.

        Parameters
        ----------
        rot : `float`
            Rotation angle in degrees.
        """
        rot_rad = np.deg2rad(rot)
        c, s = np.cos(rot_rad), np.sin(rot_rad)
        return np.array(((c, -s), (s, c)))


if __name__ == "__main__":
    pass
