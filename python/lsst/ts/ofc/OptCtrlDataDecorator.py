import os
import numpy as np

from lsst.ts.ofc.Decorator import Decorator
from lsst.ts.wep.ParamReader import ParamReader
from lsst.ts.ofc.BendModeToForce import BendModeToForce
from lsst.ts.ofc.Utility import DofGroup


class OptCtrlDataDecorator(Decorator):

    def __init__(self, decoratedObj):
        """Initialization of optimal control data decorator class.

        Parameters
        ----------
        decoratedObj : obj
            Decorated object.
        """

        super(OptCtrlDataDecorator, self).__init__(decoratedObj)

        self.xRef = ""

        self._authority = np.array([])
        self._rigidBodyStrokeFile = ParamReader()
        self._weightingFile = ParamReader()
        self._pssnAlphaFile = ParamReader()
        self._configOptCtrlFile = ParamReader()

    def configOptCtrlData(self, configFileName="optiPSSN.yaml",
                          weightingFileName="imgQualWgt.yaml",
                          pssnAlphaFileName="pssnAlpha.yaml",
                          rigidBodyStrokeFileName="rbStroke.yaml",
                          m1m3ActuatorForceFileName="M1M3_1um_156_force.yaml",
                          m2ActuatorForceFileName="M2_1um_72_force.yaml"):
        """Do the configuration of OptCtrlDataDecorator class.

        Parameters
        ----------
        configFileName : str, optional
            Name of configuration file. (the default is "optiPSSN.yaml".)
        weightingFileName : str, optional
            Weighting file name for image quality. (the default is
            "imgQualWgt.yaml".)
        pssnAlphaFileName : str, optional
            Normalized point source sensitivity (PSSN) alpha file name.
            (the default is "pssnAlpha.yaml".)
        rigidBodyStrokeFileName : str, optional
            Rigid body stroke file name. (the default is "rbStroke.yaml".)
        m1m3ActuatorForceFileName : str, optional
            M1M3 actuator force file name. (the default is
            "M1M3_1um_156_force.yaml".)
        m2ActuatorForceFileName : str, optional
            M2 actuator force file name. (the default is
            "M2_1um_72_force.yaml".)
        """

        rigidBodyStrokeFilePath = os.path.join(self.getConfigDir(),
                                               rigidBodyStrokeFileName)
        self._rigidBodyStrokeFile.setFilePath(rigidBodyStrokeFilePath)

        weightingFilePath = os.path.join(self.getInstDir(), weightingFileName)
        self._weightingFile.setFilePath(weightingFilePath)

        pssnAlphaFilePath = os.path.join(self.getConfigDir(),
                                         pssnAlphaFileName)
        self._pssnAlphaFile.setFilePath(pssnAlphaFilePath)

        configOptCtrlFilePath = os.path.join(self.getConfigDir(),
                                             configFileName)
        self._configOptCtrlFile.setFilePath(configOptCtrlFilePath)
        self.xRef = self._getXref()
        self._setAuthority(m1m3ActuatorForceFileName, m2ActuatorForceFileName)

    def _getXref(self):
        """Get the reference point in the control algorithm.

        Returns
        -------
        str
            Reference point.

        Raises
        ------
        ValueError
            The xRef is not in the xRefList.
        """

        xRef = self._configOptCtrlFile.getSetting("xref")
        xRefList = self._configOptCtrlFile.getSetting("xrefList")

        if xRef not in xRefList:
            raise ValueError("The xRef(%s) is not in the xRefList." % xRef)

        return xRef

    def _setAuthority(self, m1m3ActuatorForceFileName, m2ActuatorForceFileName):
        """Set the authority of subsystems.

        The penality is considered. The array order is [M2 hexapod,
        camera hexapod, M1M3 bending mode, M2 bending mode].

        Parameters
        ----------
        m1m3ActuatorForceFileName : str
            M1M3 actuator force file name.
        m2ActuatorForceFileName : str
            M2 actuator force file name.
        """

        rbStrokeAuthority = self._calcRigidBodyAuth()

        m1m3Authority = self._calcMirrorAuth(
            DofGroup.M1M3Bend, m1m3ActuatorForceFileName)
        m2Authority = self._calcMirrorAuth(
            DofGroup.M2Bend, m2ActuatorForceFileName)

        penality = self.getPenality()
        self._authority = np.concatenate((rbStrokeAuthority,
                                         penality["M1M3Act"] * m1m3Authority,
                                         penality["M2Act"] * m2Authority))

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
        rbStrokeFloat = list(map(float, rbStroke))

        return rbStrokeFloat

    def _calcMirrorAuth(self, dofGroup, actuatorForceFileName):
        """Calculate the distribution of control authority of mirror.

        This is based on the standard deviation of actuator forces for each
        bending mode is used. The unit is 1 N RMS.

        DOF: degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.
        actuatorForceFileName : str
            Mirror actuator force file name.

        Returns
        -------
        numpy.ndarray
            Authority of mirror.
        """

        bendingModeToForce = BendModeToForce()
        bendingModeToForce.config(self.configDir, dofGroup,
                                  actuatorForceFileName)
        bendingMode = bendingModeToForce.getRotMat()

        return np.std(bendingMode, axis=0)

    def getAuthority(self):
        """Get the authority of subsystems.

        The penality is considered. The array order is [M2 hexapod,
        camera hexapod, M1M3 bending mode, M2 bending mode].

        Returns
        -------
        numpy.ndarray
            Authority of subsystem.
        """

        return self._authority

    def getQwgt(self):
        """Get the weighting ratio of image quality.

        This is used in the Q matrix calculation.

        Returns
        -------
        numpy.ndarray
            Weighting ratio for the iamge quality Q matrix calculation.
        """

        qWgtDict = self._weightingFile.getContent()
        qWgt = self._appendDictValuesToArray(qWgtDict)

        # Do the normalization
        qWgtNormalized = qWgt/np.sum(qWgt)

        return qWgtNormalized

    def getPssnAlpha(self):
        """Get the PSSN alpha value.

        PSSN: Normalized point source sensitivity.

        Returns
        -------
        numpy.ndarray
            PSSN alpha.
        """

        pssnAlpha = self._pssnAlphaFile.getSetting("alpha")

        return np.array(pssnAlpha)

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
        motRng = 1 / self.getAuthority() * rbStroke[0]

        return motRng

    def getState0FromFile(self, state0InDofFileName="state0inDof.yaml"):
        """Get the state 0 in degree of freedom (DOF) from the file.

        Parameters
        ----------
        state0InDofFileName : str, optional
            File name to read the telescope state 0, which depends on the
            instrument. (the default is "state0inDof.yaml".)

        Returns
        -------
        numpy.ndarray
            State 0.
        """

        filePath = os.path.join(self.getInstDir(), state0InDofFileName)
        paramReader = ParamReader(filePath=filePath)
        state0InDofDict = paramReader.getContent()
        state0InDof = self._appendDictValuesToArray(state0InDofDict)

        return state0InDof

    def getPenality(self):
        """Get the penality of subsystems.

        Returns
        -------
        dict
            Penality of subsystems.
        """

        penality = {}
        penality["M1M3Act"] = float(self._configOptCtrlFile.getSetting(
            "m1M3ActuatorPenalty"))
        penality["M2Act"] = float(self._configOptCtrlFile.getSetting(
            "m2ActuatorPenalty"))
        penality["Motion"] = float(self._configOptCtrlFile.getSetting(
            "motionPenalty"))
        return penality

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
