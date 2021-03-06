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

from lsst.ts.ofc.Utility import DofGroup, rot1dArray
from lsst.ts.wep.ParamReader import ParamReader


class BendModeToForce(object):

    RCOND = 1e-4

    def __init__(self):
        """Initialization of bending mode to force class."""

        # Rotation matrix to rotate the basis from bending mode to actuator
        # forces
        self.rotMat = np.array([])

    def config(self, configDir, dofGroup, bendingModeFileName):
        """Do the configuration of BendModeToForce class.

        DOF: Degree of freedom.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        dofGroup : enum 'DofGroup'
            DOF group.
        bendingModeFileName : str
            Bending mode file name.
        """

        mirrorDirName = self.getMirrorDirName(dofGroup)
        bendModeFilePath = os.path.join(configDir, mirrorDirName, bendingModeFileName)
        bendingModeFile = ParamReader(filePath=bendModeFilePath)

        self.rotMat = self._getMirRotMat(configDir, dofGroup, bendingModeFile)

    @staticmethod
    def getMirrorDirName(dofGroup):
        """Get the mirror directory name in the configuration directory.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.

        Returns
        -------
        str
            Mirror directory name
        """

        BendModeToForce.checkDofGroupIsMirror(dofGroup)

        if dofGroup == DofGroup.M1M3Bend:
            mirrorDirName = "M1M3"
        elif dofGroup == DofGroup.M2Bend:
            mirrorDirName = "M2"

        return mirrorDirName

    @staticmethod
    def checkDofGroupIsMirror(dofGroup):
        """Check the input DOF group is mirror.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group (M1M3Bend or M2Bend).

        Raises
        ------
        ValueError
            The input DOF group is not mirror.
        """

        if dofGroup not in (DofGroup.M1M3Bend, DofGroup.M2Bend):
            raise ValueError("The input DOF group (%s) is not mirror." % dofGroup)

    def _getMirRotMat(
        self, configDir, dofGroup, bendingModeFile, idxDofFileName="idxDOF.yaml"
    ):
        """Get the mirror rotation matrix.

        DOF: Degree of freedom.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        dofGroup : enum 'DofGroup'
            DOF group.
        bendingModeFile : lsst.ts.wep.ParamReader
            Bending mode file.
        idxDofFileName : str, optional
            Index of DOF file name. (the default is "idxDOF.yaml".)

        Returns
        -------
        numpy.ndarray
            Mirror rotation matrix.
        """

        # Get the number of bending mode
        idxDofFilePath = os.path.join(configDir, idxDofFileName)
        idxDofFile = ParamReader(filePath=idxDofFilePath)
        numOfBendingMode = self._getNumOfBendingMode(dofGroup, idxDofFile)

        # Get the bending mode
        # The first three terms (actuator ID in ZEMAX, x position in m,
        # y position in m) are not needed.
        usecols = np.arange(3, 3 + numOfBendingMode)
        mat = bendingModeFile.getMatContent()
        rotMat = mat[:, usecols]

        return rotMat

    def _getNumOfBendingMode(self, dofGroup, idxDofFile):
        """Get the number of bending mode to use.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.
        idxDofFile : lsst.ts.wep.ParamReader
            Index of DOF file.

        Returns
        -------
        int
            Number of bending mode.
        """

        BendModeToForce.checkDofGroupIsMirror(dofGroup)

        if dofGroup == DofGroup.M1M3Bend:
            groupName = "m1M3Bend"
        elif dofGroup == DofGroup.M2Bend:
            groupName = "m2Bend"

        numOfBendingMode = idxDofFile.getSetting(groupName).get("idxLength")

        return int(numOfBendingMode)

    def getRotMat(self):
        """Get the rotation matrix.

        Returns
        -------
        numpy.ndarray
            Rotation matrix.
        """

        return self.rotMat

    def calcActForce(self, mirrorDof):
        """Calculate the actuator forces in N based on the degree of freedom
        (DOF).

        Parameters
        ----------
        mirrorDof : numpy.ndarray
            Mirror DOF in um.

        Returns
        -------
        numpy.ndarray
            Actuator forces in N
        """

        return rot1dArray(mirrorDof, self.rotMat)

    def estiBendingMode(self, actForce):
        """Estimate the bending mode.

        Parameters
        ----------
        actForce : numpy.ndarray
            Actuator forces in N.

        Returns
        -------
        numpy.ndarray
            Estimated bending mode in um.
        """

        pinvRotMat = np.linalg.pinv(self.rotMat, rcond=self.RCOND)

        return rot1dArray(actForce, pinvRotMat)


if __name__ == "__main__":
    pass
