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

import numpy as np
from scipy.linalg import block_diag

from lsst.ts.ofc.Utility import DofGroup


class CamRot(object):
    def __init__(self, rotAngInDeg=0):
        """Initialization of camera rotation class.

        Parameters
        ----------
        rotAngInDeg : float, optional
            Rotation angle in degree. (the default is 0.)
        """

        self.rotAngInDeg = rotAngInDeg

    def setRotAng(self, rotAngInDeg):
        """Set the rotation angle in degree.

        Parameters
        ----------
        rotAngInDeg : float
            Rotation angle in degree.

        Raises
        ------
        ValueError
            Camera rotation angle should be in [-90, 90].
        """

        if np.abs(rotAngInDeg) <= 90:
            self.rotAngInDeg = rotAngInDeg
        else:
            raise ValueError("Camera rotation angle should be in [-90, 90].")

    def getRotAng(self):
        """Get the rotation angle in degree.

        Returns
        -------
        float
            Rotation angle.
        """

        return self.rotAngInDeg

    def rotGroupDof(self, dofGroup, stateInDof, tiltXYinArcsec=(0, 0)):
        """Rotate the degree of freedom of specific group.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.
        stateInDof : numpy.ndarray or list
            State in degree of freedom (DOF).
        tiltXYinArcsec : tuple, optional
            Tilt angle in arcsec. This is the delta value of M2 hexapod
            compared with camera hexapod (M2-camera).

        Returns
        -------
        numpy.ndarray
            Rotated DOF.
        """

        # 1 arcsec = 1/3600 deg
        tiltXYinDeg = tuple(ti / 3600.0 for ti in tiltXYinArcsec)

        stateInDof = np.array(stateInDof, dtype=float)
        if dofGroup in (DofGroup.M2HexPos, DofGroup.CamHexPos):
            rotatedStateInDof = self._rotHexPos(dofGroup, stateInDof, tiltXYinDeg)
        elif dofGroup in (DofGroup.M1M3Bend, DofGroup.M2Bend):
            rotatedStateInDof = self._rotBendingMode(dofGroup, stateInDof, tiltXYinDeg)

        return rotatedStateInDof

    def _rotHexPos(self, dofGroup, hexPos, tiltXYinDeg):
        """Rotate the hexapod position (degree of freedom, DOF) based on the
        rotation angle.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.
        hexPos : numpy.ndarray
            Hexapod position: (z, x, y, rx, ry). x, y, and z are in um. rx and
            ry are in arcsec.
        tiltXYinDeg : tuple
            Tilt angle in degree. This is the delta value of M2 hexapod
            compared with camera hexapod (M2-camera).

        Returns
        -------
        numpy.ndarray
            Rotated position.
        """

        if dofGroup == DofGroup.M2HexPos:
            rotAngInDeg = self._mapRotAngByTiltXY(self.rotAngInDeg, tiltXYinDeg)
        elif dofGroup == DofGroup.CamHexPos:
            rotAngInDeg = self.rotAngInDeg

        rotMat = self._getHexRotMat(rotAngInDeg)
        rotatedHexPos = rotMat.dot(hexPos.reshape(-1, 1))

        return rotatedHexPos.ravel()

    def _mapRotAngByTiltXY(self, rotAngInDeg, tiltXYinDeg):
        """Map the rotation angle by tilt x, y axis.

        The input rotation angle (theta') is defined on x', y'-plane, which is
        tilted from x, y-plane. The output rotation angle (theta) is defined
        on x, y-plane. The tilt angles in inputs are defined as tilt x'-x and
        tilt y'-y.

        Parameters
        ----------
        rotAngInDeg : float
            Rotation angle in degree.
        tiltXYinDeg : tuple
            Tilt angle (x, y) in degree.

        Returns
        -------
        float
            Mapped rotation angle in degree.
        """

        # theta = atan(  tan(theta') * (1 - tilt-x + tilt-y) )
        theta = np.deg2rad(rotAngInDeg)
        tiltXinRad = np.deg2rad(tiltXYinDeg[0])
        tiltYinRad = np.deg2rad(tiltXYinDeg[1])

        mappedTheta = np.arctan(np.tan(theta) * (1 - tiltXinRad + tiltYinRad))

        return np.rad2deg(mappedTheta)

    def _getHexRotMat(self, rotAngInDeg):
        """Get the hexapod rotation matrix.

        Parameters
        ----------
        rotAngInDeg : float
            Rotation angle in degree.

        Returns
        -------
        numpy.ndarray
            Hexapod rotation matrix.
        """

        rotMat = self._calcRotMat(rotAngInDeg)

        return block_diag(1, rotMat, rotMat)

    def _calcRotMat(self, rotAngInDeg):
        """Calculate the 2D rotation matrix.

        Parameters
        ----------
        rotAngInDeg : float
            Rotation angle in degree.

        Returns
        -------
        numpy.ndarray
            Rotation matrix.
        """

        theta = np.deg2rad(rotAngInDeg)
        c, s = np.cos(theta), np.sin(theta)
        R = np.array(((c, -s), (s, c)))

        return R

    def _rotBendingMode(self, dofGroup, bendingMode, tiltXYinDeg):
        """Rotate the bending mode (degree of freedom, DOF) based on the
        rotation angle and tilt angle compared with the camera.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.
        bendingMode : numpy.ndarray
            20 mirror bending mode.
        tiltXYinDeg : tuple
            Tilt angle in degree. This is the delta value of M2 hexapod
            compared with camera hexapod (M2-camera).

        Returns
        -------
        numpy.ndarray
            Rotated bending mode.
        """

        rotAngInDeg = self._mapRotAngByTiltXY(self.rotAngInDeg, tiltXYinDeg)
        rotMat = self._getMirRotMat(dofGroup, rotAngInDeg)
        rotatedBendingMode = rotMat.dot(bendingMode.reshape(-1, 1))

        return rotatedBendingMode.ravel()

    def _getMirRotMat(self, dofGroup, rotAngInDeg):
        """Get the mirror rotation matrix.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.
        rotAngInDeg : float
            Rotation angle in degree.

        Returns
        -------
        numpy.ndarray
            Mirror rotation matrix.
        """

        rotMat = self._calcRotMat(rotAngInDeg)

        if dofGroup == DofGroup.M1M3Bend:
            return block_diag(
                rotMat,
                1,
                rotMat,
                rotMat,
                rotMat,
                rotMat,
                1,
                rotMat,
                rotMat,
                rotMat,
                1,
                1,
            )
        elif dofGroup == DofGroup.M2Bend:
            return block_diag(
                rotMat,
                rotMat,
                1,
                rotMat,
                rotMat,
                rotMat,
                rotMat,
                rotMat,
                rotMat,
                rotMat,
                1,
            )


if __name__ == "__main__":
    pass
