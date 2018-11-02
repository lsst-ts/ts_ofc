import os
import re
import numpy as np

from lsst.ts.ofc.Utility import InstName, getMatchFilePath, \
                                getDirFiles, getSetting

from lsst.ts.ofc.OptStateEsti import OptStateEsti


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

    def setGain(self, gain):
        """Set the gain value.

        Parameters
        ----------
        gain : float
            Gain value in the feedback. It should be in the range of 0 and 1.
        
        Raises
        ------
        ValueError
            Gain is not in the range of [0, 1].
        """
        
        if (0 <= gain <= 1):
            self.gain = gain
        else:
            raise ValueError("Gain is not in the range of [0, 1].")

    def getGain(self):
        """Get the gain value.

        Returns
        -------
        float
            Gain value in the feedback.
        """
        
        return self.gain

    def setState0(self, state0InDof):
        """Set the state 0 in degree of freedom (DOF).

        Parameters
        ----------
        state0InDof : numpy.ndarray or list
            State 0 in DOF.
        """
        
        self.state0InDof = np.array(state0InDof)

    def setState(self, stateInDof):
        """Set the state in degree of freedom (DOF).

        Parameters
        ----------
        stateInDof : numpy.ndarray or list
            State in DOF.
        """
        
        self.stateInDof = np.array(stateInDof)

    def getState0(self, dofIdx):
        """Get the state 0 in degree of freedom (DOF).

        Parameters
        ----------
        dofIdx : numpy.ndarray[int] or list[int]
            Index array of degree of freedom.

        Returns
        -------
        numpy.ndarray
            State 0 in DOF.
        """
        
        return self.state0InDof[dofIdx]

    def getState(self, dofIdx):
        """Get the state in degree of freedom (DOF).

        Parameters
        ----------
        dofIdx : numpy.ndarray[int] or list[int]
            Index array of degree of freedom.

        Returns
        -------
        numpy.ndarray
            State in DOF.
        """
        
        return self.stateInDof[dofIdx]

    def getNumOfState0(self):
        """Get the number of element of state 0.

        Returns
        -------
        int
            Number of element of state 0.
        """
        
        return len(self.state0InDof)

    def aggState(self, calcDof, dofIdx):
        """Aggregate the calculated degree of freedom (DOF) in the state.

        Parameters
        ----------
        calcDof : numpy.ndarray
            Calculated DOF.
        dofIdx : numpy.ndarray[int] or list[int]
            Index array of degree of freedom.
        """
        
        addDof = np.zeros(self.getNumOfState0())
        addDof[dofIdx] = calcDof

        self.stateInDof += addDof

    def getDofFromFile(self, dofFilePath):
        """Get the degree of freedom (DOF) from file.

        Parameters
        ----------
        dofFilePath : str
            DOF file path.
        
        Returns
        -------
        numpy.ndarray
            DOF.
        """
        
        return np.loadtxt(dofFilePath, usecols=1)

    def getGroupDof(self, startIdx, groupLeng, inputDof=None):
        """Get the degree of freedom (DOF) of specific group based on the
        start index and length.

        If there is no input DOF, the output will be the aggregated DOF
        (state - state0). Otherwise, the output is based on the input DOF.

        The default output units are:
        1. M2 hexapod position (dz in um, dx in um, dy in um, rx in arcsec,
        ry in arcsec).
        2. Cam hexapod position (dz in um, dx in um, dy in um, rx in arcsec,
        ry in arcsec).
        3. M1M3 20 bending mode in um.
        4. M2 20 bending mode in um.

        Parameters
        ----------
        startIdx : int
            Start index of group.
        groupLeng : int
            Index length of group.
        inputDof : numpy.ndarray or list, optional
            Input DOF. (the default is None.)

        Returns
        -------
        numpy.ndarray
            DOF.
        """

        if (inputDof is None):
            dof = self.stateInDof - self.state0InDof 
        else:
            dof = np.array(inputDof)

        return dof[np.arange(startIdx, startIdx+groupLeng)]

    def setMatF(self, zn3Idx, dofIdx, effWave, senM):
        """Set the F matrix. 

        F = inv(A.T * C.T * C * A + rho * H).

        Parameters
        ----------
        zn3Idx : numpy.ndarray[int] or list[int]
            Index array of z3 to zn.
        dofIdx : numpy.ndarray[int] or list[int]
            Index array of degree of freedom.
        effWave : float
            Effective wavelength in um.
        senM : numpy.ndarray
            Sensitivity matrix M.
        """

        matH = self._getMatH(dofIdx)

        qWgt = self._getQwgtFromFile()
        pssnAlpha = self._getPssnAlphaFromFile()
        ccMat = self._calcCCmat(pssnAlpha, effWave, zn3Idx)
        qMat = self._calcQmat(ccMat, senM, qWgt)

        self.matF = self._calcF(qMat, matH)

    def _getQwgtFromFile(self):
        """Get the weighting ratio of image quality from file. This is
        used in the Q matrix calculation.

        Returns
        -------
        numpy.ndarray
            Weighting ratio for the iamge quality Q matrix calculation.
        """

        filePath = os.path.join(self._getInstDir(), self.weightingFileName)
        qWgt = np.loadtxt(filePath, usecols=1)

        # Do the normalization
        qWgt = qWgt/np.sum(qWgt)

        return qWgt

    def _getPssnAlphaFromFile(self):
        """Get the PSSN alpha value from file.
        
        PSSN: Normalized point source sensitivity.
        
        Returns
        -------
        numpy.ndarray
            PSSN alpha.
        """
        
        filePath = os.path.join(self.configDir, self.pssnAlphaFileName)
        pssnAlpha = np.loadtxt(filePath, usecols=0)

        return pssnAlpha

    def _getMatH(self, dofIdx):
        """Get the matrix H used in the control algorithm.

        This matrix has considered the affection of penality on the
        authority of groups.

        Parameters
        ----------
        dofIdx : numpy.ndarray[int] or list[int]
            Index array of degree of freedom.
        
        Returns
        -------
        numpy.ndarray
            Matrix H used in the cost function.
        """
        
        authority = self.authority[dofIdx]
        matH = np.diag(authority**2)

        return matH

    def _calcCCmat(self, pssnAlpha, effWave, zn3Idx):
        """Calculate the CC matrix used in matrix Q. It is C.T * C
        used in Q = A.T * (C.T * C) * A.
        
        Cost function: J = x.T * Q * x + rho * u.T * H * u
        Choose x.T * Q * x = p.T * p
        p = C * y = C * (A * x)
        p.T * p = (C * A * x).T * C * A * x 
                = x.T * (A.T * C.T * C * A) * x = x.T * Q * x
        CCmat is C.T *C above
        
        Parameters
        ----------
        pssnAlpha : numpy.ndarray
            PSSN alpha.
        effWave : float
            Effective wavelength in um.
        zn3Idx : numpy.ndarray[int] or list[int]
            Index array of z3 to zn.
        
        Returns
        -------
        numpy.ndarray
            C.T * C matrix.
        """
        
        ccMat = (2*np.pi/effWave)**2 * pssnAlpha[zn3Idx]
        ccMat = np.diag(ccMat)

        return ccMat

    def _calcQmat(self, ccMat, senM, qWgt):
        """Calculate the Q matrix used in the cost function.

        Parameters
        ----------
        ccMat : numpy.ndarray
            C.T * C matrix.
        senM : numpy.ndarray
            Sensitivity matrix M.
        qWgt : numpy.ndarray
            Weighting ratio for the iamge quality Q matrix calculation.

        Returns
        -------
        numpy.ndarray
            Q matrix used in cost functin.
        """

        # Qi = A.T * C.T * C * A for each field point 
        # Final Q := sum_i (wi * Qi)        
        qMat = 0
        for aMat, wgt in zip(senM, qWgt):
            qMat += wgt * aMat.T.dot(ccMat).dot(aMat)

        return qMat

    def _calcF(self, qMat, matH):
        """Calculate the F matrix. F = inv(A.T * C.T * C * A + rho * H).
        
        u = - A.T * C.T * C * A / (A.T * C.T * C * A + rho * H) * x0
          = - F * (A.T * C.T * C * A) * x0
        F = inv( A.T * C.T * C * A + rho * H )
        Q = A.T * C.T * C * A
        
        Parameters
        ----------
        qMat : numpy.ndarray
            Q matrix used in cost functin.
        matH : numpy.ndarray
            Matrix H used in the cost function.
        
        Returns
        -------
        numpy.ndarray
            F matrix.
        """
        
        # Because the unit is rms^2, the square of rho read from
        # the *.ctrl file is needed.
        matF = np.linalg.inv(self.penality["Motion"]**2 * matH + qMat)

        return matF

    def getMatF(self):
        """Get the F matrix.

        F = inv(A.T * C.T * C * A + rho * H).

        Returns
        -------
        numpy.ndarray
            F matrix.
        """

        return self.matF

    def getNumOfFieldInQwgt(self):
        """Get the number of field in the image quality weighting ratio.

        Returns
        -------
        int
            Number of field for the image quality weighting ratio.
        """
        
        qWgt = self._getQwgtFromFile()

        return len(qWgt)

    def calcEffGQFWHM(self):
        pass

    def getMotRng(self):
        pass

    def estiUk(self):
        pass

    def _calcUkRef0(self):
        pass

    def _calcUkRefX00(self):
        pass

    def _calcUkRefX0(self):
        pass

    def _calcUk(self):
        pass

    def _calcQx(self):
        pass


if __name__ == "__main__":
    
    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"
    optCtrl = OptCtrl()
    optCtrl.config(configDir, instName=InstName.LSST)
    optCtrl.setGain(1)

    # dofIdx = [2,3,4,5]
    # calcDof = [0.1, 0.2, 0.3, 0.4]
    # optCtrl.aggState(calcDof, dofIdx)
    # print(optCtrl.getState(dofIdx))

    dofFilePath = "/home/ttsai/Documents/github/ts_tcs_ofcPython/tests/testData/lsst_pert_iter1.txt"
    dof = optCtrl.getDofFromFile(dofFilePath)

    optStateEsti = OptStateEsti()
    optStateEsti.config(configDir, instName=InstName.LSST)

    effWave = 0.5
    senM = optStateEsti.senM
    dofIdx = optStateEsti.dofIdx
    zn3Idx = optStateEsti.zn3Idx
    optCtrl.setMatF(zn3Idx, dofIdx, effWave, senM)
    print(optCtrl.getNumOfFieldInQwgt())
