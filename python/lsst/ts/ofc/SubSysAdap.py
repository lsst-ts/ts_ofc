import os
import numpy as np

from lsst.ts.wep.ParamReader import ParamReader
from lsst.ts.ofc.BendModeToForce import BendModeToForce
from lsst.ts.ofc.Utility import DofGroup, rot1dArray


class SubSysAdap(object):

    def __init__(self):
        """Initialization of subsystem adaptor class."""

        # The row is in the ZEMAX basis. The column is in the subsystem basis.
        self.rotMatM1M3Bend = np.array([])
        self.rotMatM2Bend = np.array([])

        self.rotMatM1M3Act = 1.0
        self.rotMatM2Act = 1.0

        self.rotMatHex = np.array([])

    def config(self, configDir, rotMatM1M3FileName="rotMatM1M3.yaml",
               rotMatM2FileName="rotMatM2.yaml",
               rotMatHexpodFileName="rotMatHexapod.yaml"):
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

        self.rotMatM1M3Bend, self.rotMatM1M3Act = \
            self._getRotMatMirror(configDir, DofGroup.M1M3Bend,
                                  rotMatM1M3FileName)
        self.rotMatM2Bend, self.rotMatM2Act = \
            self._getRotMatMirror(configDir, DofGroup.M2Bend,
                                  rotMatM2FileName)
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
        numpy.ndarray
            Rotation matrix of mirror's bending mode.
        float
            Rotation matrix of mirror's actuator.
        """

        mirrorDirName = BendModeToForce.getMirrorDirName(dofGroup)
        rotMatFilePath = os.path.join(configDir, mirrorDirName, rotMatfileName)
        rotMatFile = ParamReader(filePath=rotMatFilePath)

        rotMatBend = rotMatFile.getSetting("bend")
        rotMatAct = rotMatFile.getSetting("act")

        return np.diag(rotMatBend), rotMatAct

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

    def getRotMatInDof(self, dofGroup):
        """Get the rotation matrix in the basis of DOF.

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

        rotMat = np.array([])
        if (dofGroup == DofGroup.M1M3Bend):
            rotMat = self.rotMatM1M3Bend
        elif (dofGroup == DofGroup.M2Bend):
            rotMat = self.rotMatM2Bend
        elif dofGroup in (DofGroup.M2HexPos, DofGroup.CamHexPos):
            rotMat = self.rotMatHex
        else:
            raise ValueError("The input(%s) is not supported." % dofGroup)

        return rotMat

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

        if (dofGroup == DofGroup.M1M3Bend):
            rotMat = self.rotMatM1M3Act
        elif (dofGroup == DofGroup.M2Bend):
            rotMat = self.rotMatM2Act

        return rotMat

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

    def transBendingModeToZemax(self, dofGroup, mirrorBend):
        """Transform the mirror bending mode in subsystem's coordinate to ZEMAX
        coordinate.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group (M1M3Bend or M2Bend).
        mirrorBend : numpy.ndarray
            Mirror bending mode in subsystem's coordinate.

        Returns
        -------
        numpy.ndarray
            Mirror bending mode in ZEMAX coordinate.
        """

        rotMat = self._getRotMatOfMirrorBend(dofGroup)

        return rot1dArray(mirrorBend, rotMat)

    def _getRotMatOfMirrorBend(self, dofGroup):
        """Get the rotation matrix of mirror's bending mode.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.

        Returns
        -------
        numpy.ndarray
            Rotation matrix of mirror's bending mode.
        """

        self._checkMirrorGroup(dofGroup)

        if (dofGroup == DofGroup.M1M3Bend):
            rotMat = self.rotMatM1M3Bend
        elif (dofGroup == DofGroup.M2Bend):
            rotMat = self.rotMatM2Bend

        return rotMat

    def transBendingModeToSubSys(self, dofGroup, mirrorBend):
        """Transform the mirror bending mode in ZEMAX coordinate to subsystem's
        coordinate.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group (M1M3Bend or M2Bend).
        mirrorBend : numpy.ndarray
            Mirror bending mode in ZEMAX coordinate.

        Returns
        -------
        numpy.ndarray
            Mirror bending mode in subsystem's coordinate.
        """

        rotMat = self._getRotMatOfMirrorBend(dofGroup)
        invRotMat = np.linalg.inv(rotMat)

        return rot1dArray(mirrorBend, invRotMat)

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
