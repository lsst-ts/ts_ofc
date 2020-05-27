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

import os
import numpy as np

from lsst.ts.wep.ParamReader import ParamReader
from lsst.ts.ofc.BendModeToForce import BendModeToForce
from lsst.ts.ofc.Utility import DofGroup, rot1dArray


class SubSysAdap(object):
    def __init__(self):
        """Initialization of subsystem adaptor class."""

        # Rotation matrix of M1M3 actuator force
        self.rotMatM1M3Act = 1.0

        # Rotation matrix of M2 actuator force
        self.rotMatM2Act = 1.0

        # Rotation matrix of hexapod position
        self.rotMatHex = np.array([])

    def config(
        self,
        configDir,
        rotMatM1M3FileName="rotMatM1M3.yaml",
        rotMatM2FileName="rotMatM2.yaml",
        rotMatHexpodFileName="rotMatHexapod.yaml",
    ):
        """Do the configuration of SubSysAdap class.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        rotMatM1M3FileName : str, optional
            Rotation matrix file name of M1M3. (the default is
            "rotMatM1M3.yaml".)
        rotMatM2FileName : str, optional
            Rotation matrix file name of M2. (the default is "rotMatM2.yaml".)
        rotMatHexpodFileName : str, optional
            Rotation matrix file name of hexapod. (the default is
            "rotMatHexapod.yaml".)
        """

        self.rotMatM1M3Act = self._getRotMatMirror(
            configDir, DofGroup.M1M3Bend, rotMatM1M3FileName
        )
        self.rotMatM2Act = self._getRotMatMirror(
            configDir, DofGroup.M2Bend, rotMatM2FileName
        )
        self.rotMatHex = self._getRotMatHex(configDir, rotMatHexpodFileName)

    def _getRotMatMirror(self, configDir, dofGroup, rotMatfileName):
        """Get the rotation matrix of mirror.

        DOF: Degree of freedom.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        dofGroup : enum 'DofGroup'
            DOF group.
        rotMatfileName : str
            Rotation matrix file name.

        Returns
        -------
        float
            Rotation matrix of mirror's actuator.
        """

        mirrorDirName = BendModeToForce.getMirrorDirName(dofGroup)
        rotMatFilePath = os.path.join(configDir, mirrorDirName, rotMatfileName)
        rotMatFile = ParamReader(filePath=rotMatFilePath)

        return rotMatFile.getSetting("act")

    def _getRotMatHex(self, configDir, rotMatfileName):
        """Get the rotation matrix of hexapod.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        rotMatfileName : str
            Rotation matrix file name.

        Returns
        -------
        numpy.ndarray
            Rotation matrix of hexapod.
        """

        rotMatFilePath = os.path.join(configDir, rotMatfileName)
        rotMatFile = ParamReader(filePath=rotMatFilePath)
        rotMat = rotMatFile.getMatContent()

        return rotMat

    def getRotMatHexInDof(self, dofGroup):
        """Get the rotation matrix of hexapod in the basis of DOF.

        The row is in the ZEMAX basis. The column is in the subsystem basis.
        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.

        Returns
        -------
        numpy.ndarray
            Rotation matrix.

        Raises
        ------
        ValueError
            The input is not supported.
        """

        if dofGroup in (DofGroup.M2HexPos, DofGroup.CamHexPos):
            return self.rotMatHex
        else:
            raise ValueError("The input(%s) is not supported." % dofGroup)

    def transActForceToZemax(self, dofGroup, actForce):
        """Transform the actuator forces in subsystem's coordinate to ZEMAX
        coordinate.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group (M1M3Bend or M2Bend).
        actForce : numpy.ndarray
            Actuator forces in subsystem's coordinate.

        Returns
        -------
        numpy.ndarray
            Actuator forces in ZEMAX coordinate.
        """

        rotMat = self._getRotMatOfMirrorAct(dofGroup)

        return rotMat * actForce

    def _getRotMatOfMirrorAct(self, dofGroup):
        """Get the rotation matrix of mirror's actuator.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.

        Returns
        -------
        float
            Rotation matrix of mirror's actuator.
        """

        self._checkMirrorGroup(dofGroup)

        if dofGroup == DofGroup.M1M3Bend:
            return self.rotMatM1M3Act
        elif dofGroup == DofGroup.M2Bend:
            return self.rotMatM2Act

    def _checkMirrorGroup(self, dofGroup):
        """Check the input is in the mirror group or not.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.

        Raises
        ------
        ValueError
            The input is not mirror.
        """

        if dofGroup not in (DofGroup.M1M3Bend, DofGroup.M2Bend):
            raise ValueError("The input(%s) is not mirror." % dofGroup)

    def transActForceToSubSys(self, dofGroup, actForce):
        """Transform the actuator forces in ZEMAX coordinate to subsystem's
        coordinate.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group (M1M3Bend or M2Bend).
        actForce : numpy.ndarray
            Actuator forces in ZEMAX coordinate.

        Returns
        -------
        numpy.ndarray
            Actuator forces in subsystem's coordinate.
        """

        rotMat = 1 / self._getRotMatOfMirrorAct(dofGroup)

        return rotMat * actForce

    def transHexaPosToZemax(self, hexaPos):
        """Transform the hexapod's position from subsystem's coordinate to
        ZEMAX coordinate.

        Parameters
        ----------
        hexaPos : numpy.ndarray
            Hexapod's position (x, y, z, rx, ry, rz) in subsystem's coordinate.

        Returns
        -------
        numpy.ndarray
            Hexapod's position (z', x', y', rx', ry') in ZEMAX coordinate.
        """

        return rot1dArray(hexaPos, self.rotMatHex)

    def transHexaPosToSubSys(self, hexaPos):
        """Transform the hexapod's position from ZEMAX coordinate to
        subsystem's coordinate.

        Parameters
        ----------
        hexaPos : numpy.ndarray
            Hexapod's position (z', x', y', rx', ry') in ZEMAX coordinate.

        Returns
        -------
        numpy.ndarray
            Hexapod's position (x, y, z, rx, ry, rz) in subsystem's coordinate.
        """

        invRotMat = np.linalg.pinv(self.rotMatHex)

        return rot1dArray(hexaPos, invRotMat)


if __name__ == "__main__":
    pass
