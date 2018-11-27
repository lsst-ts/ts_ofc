import os
import numpy as np

from lsst.ts.ofc.Decorator import Decorator
from lsst.ts.ofc.ParamReader import ParamReader


class OptCtrlDataDecorator(Decorator):

    def __init__(self, decoratedObj):
        """Initialization of optimal control data decorator class.

        Parameters
        ----------
        decoratedObj : obj
            Decorated object.
        """

        super(OptCtrlDataDecorator, self).__init__(decoratedObj)

        self.xRef = None
        self.authority = None
        self.penality = {"M1M3Act": 0, "M2Act": 0, "Motion": 0}

        self._rigidBodyStrokeFile = None
        self._weightingFile = None
        self._pssnAlphaFile = None
        self._configOptCtrlFile = None

    def configOptCtrlData(self, configFileName="optiPSSN_x00.ctrl",
                          weightingFileName="imgQualWgt.txt",
                          pssnAlphaFileName="pssn_alpha.txt",
                          rigidBodyStrokeFileName="rbStroke.txt",
                          m1m3ActuatorForceFileName="M1M3_1um_156_force.txt",
                          m2ActuatorForceFileName="M2_1um_force.DAT",
                          numOfBendingMode=20):
        """Do the configuration of OptCtrlDataDecorator class.

        Parameters
        ----------
        configFileName : str, optional
            Name of configuration file. (the default is "optiPSSN_x00.ctrl".)
        weightingFileName : str, optional
            Weighting file name for image quality. (the default is
            "imgQualWgt.txt".)
        pssnAlphaFileName : str, optional
            Normalized point source sensitivity (PSSN) alpha file name.
            (the default is "pssn_alpha.txt".)
        rigidBodyStrokeFileName : str, optional
            Rigid body stroke file name. (the default is "rbStroke.txt".)
        m1m3ActuatorForceFileName : str, optional
            M1M3 actuator force file name. (the default is
            "M1M3_1um_156_force.txt".)
        m2ActuatorForceFileName : str, optional
            M2 actuator force file name. (the default is "M2_1um_force.DAT".)
        numOfBendingMode : int, optional
            Number of mirror bending mode. (the default is 20.)
        """

        rigidBodyStrokeFilePath = os.path.join(self.getConfigDir(),
                                               rigidBodyStrokeFileName)
        self._rigidBodyStrokeFile = ParamReader(rigidBodyStrokeFilePath)

        weightingFilePath = os.path.join(self.getInstDir(), weightingFileName)
        self._weightingFile = ParamReader(weightingFilePath)

        pssnAlphaFilePath = os.path.join(self.getConfigDir(),
                                         pssnAlphaFileName)
        self._pssnAlphaFile = ParamReader(pssnAlphaFilePath)

        configOptCtrlFilePath = os.path.join(self.getConfigDir(),
                                             configFileName)
        self._configOptCtrlFile = ParamReader(configOptCtrlFilePath)

        self._readOptCtrlSetting()
        self._setAuthority(m1m3ActuatorForceFileName, m2ActuatorForceFileName,
                           int(numOfBendingMode))

    def _readOptCtrlSetting(self):
        """Read the configuration setting file of optimal control."""

        # Assign the reference to estimate the degree of freedom (DOF)
        self.xRef = self._configOptCtrlFile.getSetting("xref")

        # Set the penality
        self.penality["M1M3Act"] = float(self._configOptCtrlFile.getSetting(
                                                     "M1M3_actuator_penalty"))
        self.penality["M2Act"] = float(self._configOptCtrlFile.getSetting(
                                                        "M2_actuator_penalty"))
        self.penality["Motion"] = float(self._configOptCtrlFile.getSetting(
                                                            "Motion_penalty"))

    def _setAuthority(self, m1m3ActuatorForceFileName, m2ActuatorForceFileName,
                      numOfBendingMode):
        """Set the authority of subsystems.

        The penality is considered. The array order is [M2 hexapod,
        camera hexapod, M1M3 bending mode, M2 bending mode].

        Parameters
        ----------
        m1m3ActuatorForceFileName : str
            M1M3 actuator force file name.
        m2ActuatorForceFileName : str
            M2 actuator force file name.
        numOfBendingMode : int
            Number of mirror bending mode.
        """

        rbStrokeAuthority = self._calcRigidBodyAuth()

        # Skip the first three columns (M1M3 only)
        usecols = np.arange(3, 3+numOfBendingMode)
        m1m3Authority = self._calcMirrorAuth("M1M3", m1m3ActuatorForceFileName,
                                             usecols=usecols)

        usecols = np.arange(numOfBendingMode)
        m2Authority = self._calcMirrorAuth("M2", m2ActuatorForceFileName,
                                           usecols=usecols)

        self.authority = np.concatenate((rbStrokeAuthority,
                                        self.penality["M1M3Act"]*m1m3Authority,
                                        self.penality["M2Act"]*m2Authority))

    def _calcRigidBodyAuth(self):
        """Calculate the distribution of control authority of rigid body.

        The first five terms are the M2 hexapod positions. And the following
        five are the camera hexapod positions.

        Returns
        -------
        numpy.ndarray
            Authority of riigid body.
        """

        rbStroke = self._getRbStroke()
        rbStroke = np.array(rbStroke)
        authority = rbStroke[0]/rbStroke

        return authority

    def _getRbStroke(self):
        """Get the rigid body stroke.

        The order is the M2 hexapod followed by the camera hexapod.

        Returns
        -------
        list[float]
            Rigid body stroke in um.
        """

        rbStroke = self._rigidBodyStrokeFile.getSetting("rbStroke")
        rbStroke = list(map(float, rbStroke))

        return rbStroke

    def _calcMirrorAuth(self, mirrorDirName, actuatorForceFileName,
                        usecols=None):
        """Calculate the distribution of control authority of mirror.

        This is based on the standard deviation of actuator forces for each
        bending mode is used. The unit is 1 N RMS.

        Parameters
        ----------
        mirrorDirName : str
            Mirror directory name.
        actuatorForceFileName : str
            Mirror actuator force file name
        usecols : int or sequence, optional
            Which columns to read, with 0 being the first. For example,
            usecols = (1,4,5) will extract the 2nd, 5th and 6th columns.
            The default, None, results in all columns being read.

        Returns
        -------
        numpy.ndarray
            Authority of mirror.
        """

        filePath = os.path.join(self.configDir, mirrorDirName,
                                actuatorForceFileName)
        bendingMode = np.loadtxt(filePath, usecols=usecols)
        authority = np.std(bendingMode, axis=0)

        return authority

    def getAuthority(self):
        """Get the authority of subsystems.

        The penality is considered. The array order is [M2 hexapod,
        camera hexapod, M1M3 bending mode, M2 bending mode].

        Returns
        -------
        numpy.ndarray
            Authority of subsystem.
        """

        return self.authority

    def getQwgt(self):
        """Get the weighting ratio of image quality.

        This is used in the Q matrix calculation.

        Returns
        -------
        numpy.ndarray
            Weighting ratio for the iamge quality Q matrix calculation.
        """

        qWgt = self._weightingFile.getMatContent(usecols=1)

        # Do the normalization
        qWgt = qWgt/np.sum(qWgt)

        return qWgt

    def getPssnAlpha(self):
        """Get the PSSN alpha value.

        PSSN: Normalized point source sensitivity.

        Returns
        -------
        numpy.ndarray
            PSSN alpha.
        """

        pssnAlpha = self._pssnAlphaFile.getMatContent(usecols=0)

        return pssnAlpha

    def getNumOfFieldInQwgt(self):
        """Get the number of field in the image quality weighting ratio.

        Returns
        -------
        int
            Number of field for the image quality weighting ratio.
        """

        qWgt = self.getQwgt()

        return len(qWgt)

    def getMotRng(self):
        """Get the range of motion of degree of freedom (DOF).

        Returns
        -------
        numpy.ndarray
            Range of DOF, which is normalized to the unit of um.
        """

        rbStroke = self._getRbStroke()
        motRng = 1 / self.authority * rbStroke[0]

        return motRng

    def getState0FromFile(self, state0InDofFileName="state0inDof.txt"):
        """Get the state 0 in degree of freedom (DOF) from the file.

        Parameters
        ----------
        state0InDofFileName : str, optional
            File name to read the telescope state 0, which depends on the
            instrument. (the default is "state0inDof.txt".)

        Returns
        -------
        numpy.ndarray
            State 0.
        """

        filePath = os.path.join(self.getInstDir(), state0InDofFileName)
        state0InDof = np.loadtxt(filePath, usecols=1)

        return state0InDof

    def getPenality(self):
        """Get the penality of subsystems.

        Returns
        -------
        dict
            Penality of subsystems.
        """

        return self.penality

    def getXref(self):
        """Get the X reference.

        Returns
        -------
        str
            X reference.
        """

        return self.xRef


if __name__ == "__main__":
    pass
