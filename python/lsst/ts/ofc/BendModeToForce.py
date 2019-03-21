import os
import numpy as np

from lsst.ts.ofc.Utility import DofGroup, rot1dArray
from lsst.ts.ofc.ParamReaderYaml import ParamReaderYaml


class BendModeToForce(object):

    RCOND = 1e-4

    def __init__(self):
        """Initialization of bending mode to force class."""

        self.rotMat = np.array([])

    def config(self, configDir, dofGroup, bendingModeFileName):
        """Do the configuration of BendModeToForce class.

        DOF: Degree of freedom.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        dofGroup : DofGroup
            DOF group.
        bendingModeFileName : str
            Bending mode file name.
        """

        mirrorDirName = self.getMirrorDirName(dofGroup)
        bendModeFilePath = os.path.join(configDir, mirrorDirName,
                                        bendingModeFileName)
        bendingModeFile = ParamReaderYaml(filePath=bendModeFilePath)

        self.rotMat = self._getMirRotMat(configDir, dofGroup, bendingModeFile)

    @staticmethod
    def getMirrorDirName(dofGroup):
        """Get the mirror directory name in the configuration directory.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : DofGroup
            DOF group.

        Returns
        -------
        str
            Mirror directory name

        Raises
        ------
        ValueError
            The input is not a mirror group.
        """

        mirrorDirName = ""
        if (dofGroup == DofGroup.M1M3Bend):
            mirrorDirName = "M1M3"
        elif (dofGroup == DofGroup.M2Bend):
            mirrorDirName = "M2"
        else:
            raise ValueError("The input(%s) is not a mirror group." % dofGroup)

        return mirrorDirName

    def _getMirRotMat(self, configDir, dofGroup, bendingModeFile,
                      idxDofFileName="idxDOF.yaml"):
        """Get the mirror rotation matrix.

        DOF: Degree of freedom.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        dofGroup : DofGroup
            DOF group.
        bendingModeFile : ParamReaderYaml
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
        idxDofFile = ParamReaderYaml(filePath=idxDofFilePath)
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
        dofGroup : DofGroup
            DOF group.
        idxDofFile : ParamReaderYaml
            Index of DOF file.

        Returns
        -------
        int
            Number of bending mode.

        Raises
        ------
        ValueError
            The input is not a mirror group.
        """

        groupName = ""
        if (dofGroup == DofGroup.M1M3Bend):
            groupName = "m1M3Bend"
        elif (dofGroup == DofGroup.M2Bend):
            groupName = "m2Bend"
        else:
            raise ValueError("The input(%s) is not a mirror group." % dofGroup)

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
