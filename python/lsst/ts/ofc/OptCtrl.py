import os
import re
import numpy as np

from lsst.ts.ofc.Utility import InstName, getMatchFilePath, \
                                getDirFiles, getSetting


class OptCtrl(object):

    def __init__(self):
        """Initialization of optimal control class."""
        
        self.configDir = None
        self.instName = None
        self.rigidBodyStrokeFileName = None
        self.weightingFileName = None
        self.pssnAlphaFileName = None
        
        self.strategy = None
        self.xRef = None
        self.gain = 0
        self.penality = {"M1M3Act":0, "M2Act":0, "Motion":0}
        self.authority = None
        self.matF = None
        self.state0InDof = None
        self.stateInDof = None

    def config(self, configDir, instName=InstName.LSST,
               configFileName="optiPSSN_x00.ctrl",
               state0InDofFileName="state0inDof.txt",
               weightingFileName="imgQualWgt.txt",
               pssnAlphaFileName="pssn_alpha.txt",
               rigidBodyStrokeFileName="rbStroke.txt",
               m1m3ActuatorForceFileName="M1M3_1um_156_force.txt",
               m2ActuatorForceFileName="M2_1um_force.DAT",
               numOfBendingMode=20):
        """Do the configuration of optimal control.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        instName : enum 'InstName', optional
            Instrument name. (the default is InstName.LSST.)
        configFileName : str, optional
            Name of configuration file. (the default is "optiPSSN_x00.ctrl",
            which minimizes the cost function with reference point 'x00'.)
        state0InDofFileName : str, optional
            File name to read the telescope state 0, which depends on the
            instrument. (the default is "state0inDof.txt".)
        weightingFileName : str, optional
            Weighting file name for image quality. (the default is
            "imgQualWgt.txt".)
        pssnAlphaFileName : str, optional
            PSSN alpha file name. (the default is "pssn_alpha.txt".)
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

        # Assign the attributes
        self.configDir = configDir
        self.instName = instName
        self.rigidBodyStrokeFileName = rigidBodyStrokeFileName
        self.weightingFileName = weightingFileName
        self.pssnAlphaFileName = pssnAlphaFileName

        # Read the setting file
        self._readSetting(configFileName)

        # Set the state0 and state
        self._setState0ByFile(state0InDofFileName)
        self.initStateToState0()

        # Set the authority
        self._setAuthority(m1m3ActuatorForceFileName, m2ActuatorForceFileName,
                           int(numOfBendingMode))

    def _readSetting(self, configFileName):
        """Read the configuration setting file of optimal control.

        Parameters
        ----------
        configFileName : str
            Name of configuration file.
        """

        filePath = os.path.join(self.configDir, configFileName)

        # Assign the strategy to estimate the degree of freedom (DOF)
        self.strategy = getSetting(filePath, "control_strategy")
        self.xRef = getSetting(filePath, "xref")

        # Set the penalities
        self.penality["M1M3Act"] = float(getSetting(filePath,
                                                    "M1M3_actuator_penalty"))
        self.penality["M2Act"] = float(getSetting(filePath,
                                                  "M2_actuator_penalty"))
        self.penality["Motion"] = float(getSetting(filePath, "Motion_penalty"))

    def _setState0ByFile(self, state0InDofFileName):
        """Set the state 0 (x0) in degree of freedom (DOF) based on the file.

        Parameters
        ----------
        state0InDofFileName : str
            File name to read the telescope state 0, which depends on the
            instrument.
        """

        filePath = os.path.join(self._getInstDir(), state0InDofFileName)
        self.state0InDof = np.loadtxt(filePath, usecols=1)

    def _getInstDir(self):
        """Get the instrument directory.

        Returns
        -------
        str
            Instrument directory.
        """

        return os.path.join(self.configDir, self.instName.name.lower())

    def initStateToState0(self):
        """Initialize the state to the state 0 in the basis of degree of
        freedom (DOF)."""

        self.stateInDof = self.state0InDof.copy()

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

        rbStrokeAuthority = self._calcRigidBodyAuth(self.rigidBodyStrokeFileName)

        # Skip the first three columns (M1M3 only)
        usecols = np.arange(3, 3+numOfBendingMode)
        m1m3Authority = self._calcMirrorAuth("M1M3", m1m3ActuatorForceFileName, 
                                             usecols=usecols)

        usecols = np.arange(numOfBendingMode)
        m2Authority = self._calcMirrorAuth("M2", m2ActuatorForceFileName, 
                                           usecols=usecols)

        # Set the authority with the consideration of penality
        self.authority = np.concatenate((rbStrokeAuthority,
                                         self.penality["M1M3Act"]*m1m3Authority,
                                         self.penality["M2Act"]*m2Authority)) 

    def _calcRigidBodyAuth(self, rigidBodyStrokeFileName):
        """Calculate the distribution of control authority of rigid body.

        Parameters
        ----------
        rigidBodyStrokeFileName : str
            Rigid body stroke file name.

        Returns
        -------
        numpy.ndarray
            Authority of riigid body. The first fives are the M2 hexapod.
            And the following fives are the camera hexapod.
        """

        rbStroke = self._getRbStrokeFromFile(rigidBodyStrokeFileName)
        rbStroke = np.array(rbStroke)
        authority = rbStroke[0]/rbStroke

        return authority

    def _getRbStrokeFromFile(self, rigidBodyStrokeFileName):
        """Get the rigid body stroke from the file. The order is the M2
        hexapod followed by the camera hexapod.

        Parameters
        ----------
        rigidBodyStrokeFileName : str
            Rigid body stroke file name.

        Returns
        -------
        list[float]
            Rigid body stroke in um.
        """
        
        filePath = os.path.join(self.configDir, rigidBodyStrokeFileName)
        rbStroke = getSetting(filePath, "rbStroke")
        rbStroke = list(map(float, rbStroke))

        return rbStroke

    def _calcMirrorAuth(self, mirrorDirName, actuatorForceFileName,
                        usecols=None):
        """Calculate the distribution of control authority of mirror.

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
            Authority of mirror. The standard deviation of actuator forces
            for each bending mode is used. The unit is 1 N RMS.
        """

        filePath = os.path.join(self.configDir, mirrorDirName,
                                actuatorForceFileName)
        bendingMode = np.loadtxt(filePath, usecols=usecols)

        # Use the standard deviation of actuator force as an index to
        # decide the authority.
        authority = np.std(bendingMode, axis=0)

        return authority

    def calcEffGQFWHM(self):
        pass

    def getNumOfState0(self):
        pass

    def getNumOfFieldInQwgt(self):
        pass

    def setState0(self):
        pass

    def setState(self):
        pass

    def getGain(self):
        pass

    def setGain(self):
        pass

    def getState(self):
        pass

    def getState0(self):
        pass

    def getAuthority(self):
        pass

    def getMotRng(self):
        pass

    def getMatF(self):
        pass

    def getMatF(self):
        pass

    def setMatF(self):
        pass

    def estiUk(self):
        pass

    def aggState(self):
        pass

    def getDofFromFile(self):
        pass

    def getGroupDof(self):
        pass

    def _calcUkRef0(self):
        pass

    def _calcUkRefX00(self):
        pass

    def _calcUkRefX0(self):
        pass

    def _calcQmat(self):
        pass

    def _calcUk(self):
        pass

    def _calcQx(self):
        pass

    def _calcF(self):
        pass

    def _calcCCmat(self):
        pass

    def _getPssnAlpha(self):
        pass

    def _getQwgtFromFile(self):
        pass

    def _getMatH(self):
        pass


if __name__ == "__main__":
    
    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"
    optCtrl = OptCtrl()
    optCtrl.config(configDir, instName=InstName.LSST)
    authority = optCtrl._calcRigidBodyAuth(optCtrl.rigidBodyStrokeFileName)