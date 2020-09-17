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
import logging

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

        super().__init__(decoratedObj)

        self.xRef = ""

        self._authority = np.array([])
        self._rigidBodyStrokeFile = ParamReader()
        self._weightingFile = ParamReader()
        self._pssnAlphaFile = ParamReader()
        self._configOptCtrlFile = ParamReader()

    def configOptCtrlData(
        self,
        configFileName="optiPSSN.yaml",
        weightingFileName="imgQualWgt.yaml",
        pssnAlphaFileName="pssnAlpha.yaml",
        rigidBodyStrokeFileName="rbStroke.yaml",
        m1m3ActuatorForceFileName="M1M3_1um_156_force.yaml",
        m2ActuatorForceFileName="M2_1um_72_force.yaml",
    ):
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

        rigidBodyStrokeFilePath = os.path.join(
            self.getConfigDir(), rigidBodyStrokeFileName
        )
        self._rigidBodyStrokeFile.setFilePath(rigidBodyStrokeFilePath)

        weightingFilePath = os.path.join(self.getInstDir(), weightingFileName)
        self._weightingFile.setFilePath(weightingFilePath)

        pssnAlphaFilePath = os.path.join(self.getConfigDir(), pssnAlphaFileName)
        self._pssnAlphaFile.setFilePath(pssnAlphaFilePath)

        configOptCtrlFilePath = os.path.join(self.getConfigDir(), configFileName)
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
            DofGroup.M1M3Bend, m1m3ActuatorForceFileName
        )
        m2Authority = self._calcMirrorAuth(DofGroup.M2Bend, m2ActuatorForceFileName)

        penality = self.getPenality()
        self._authority = np.concatenate(
            (
                rbStrokeAuthority,
                penality["M1M3Act"] * m1m3Authority,
                penality["M2Act"] * m2Authority,
            )
        )

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
        authority = rbStroke[0] / rbStroke

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
        bendingModeToForce.config(self.configDir, dofGroup, actuatorForceFileName)
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
        qWgtNormalized = qWgt / np.sum(qWgt)

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

    def getState0FromFile(self, state0InDofFileName=None):
        """Get the state 0 in degree of freedom (DOF) from the file.

        Parameters
        ----------
        state0InDofFileName : str, optional
            File name to read the telescope state 0, which depends on the
            instrument. The file is assumed to reside in self.getInstDir()
            directory. If None (which is default), assuming it is
            "state0InDof.yaml".

        Returns
        -------
        numpy.ndarray
            State 0.
        """

        if state0InDofFileName is None:
            state0InDofFileName = "state0inDof.yaml"

        filePath = os.path.join(self.getInstDir(), state0InDofFileName)
        logging.getLogger("lsst.ts.ofc").debug(
            f"Reading 0 state configuration from {filePath}"
        )
        return self.getState0FromDict(ParamReader(filePath=filePath).getContent())

    def getState0FromDict(self, state0InDofDict):
        """Returns state 0 in degree of freedom (DOF) from dictionary.

        Parameters
        ----------
        state0InDofDict : dict
            State 0 DoF dictionary. Must contain all required fields - M2 &
            Camera hexapod, M2 & M1M3 bending modes. For hexapod, dZ,dX,dY,rX
            and rY values must be provided. mode1 through mode20 shall be
            supplied for bending modes. "M2Hexapod", "cameraHexapod",
            "M1M3Bending" and "M2Bending" are names of structures holding the
            values.

        Returns
        -------
        numpy.ndarray
            State 0.

        Raises
        ------
        ValueError
            state0InDofDict doesn't contain all required fields.
        """

        return self._appendDictValuesToArray(
            state0InDofDict,
            [
                ["M2Hexapod", "dZ"],
                ["M2Hexapod", "dX"],
                ["M2Hexapod", "dY"],
                ["M2Hexapod", "rX"],
                ["M2Hexapod", "rY"],
                ["cameraHexapod", "dZ"],
                ["cameraHexapod", "dX"],
                ["cameraHexapod", "dY"],
                ["cameraHexapod", "rX"],
                ["cameraHexapod", "rY"],
                ["M1M3Bending", "mode1"],
                ["M1M3Bending", "mode2"],
                ["M1M3Bending", "mode3"],
                ["M1M3Bending", "mode4"],
                ["M1M3Bending", "mode5"],
                ["M1M3Bending", "mode6"],
                ["M1M3Bending", "mode7"],
                ["M1M3Bending", "mode8"],
                ["M1M3Bending", "mode9"],
                ["M1M3Bending", "mode10"],
                ["M1M3Bending", "mode11"],
                ["M1M3Bending", "mode12"],
                ["M1M3Bending", "mode13"],
                ["M1M3Bending", "mode14"],
                ["M1M3Bending", "mode15"],
                ["M1M3Bending", "mode16"],
                ["M1M3Bending", "mode17"],
                ["M1M3Bending", "mode18"],
                ["M1M3Bending", "mode19"],
                ["M1M3Bending", "mode20"],
                ["M2Bending", "mode1"],
                ["M2Bending", "mode2"],
                ["M2Bending", "mode3"],
                ["M2Bending", "mode4"],
                ["M2Bending", "mode5"],
                ["M2Bending", "mode6"],
                ["M2Bending", "mode7"],
                ["M2Bending", "mode8"],
                ["M2Bending", "mode9"],
                ["M2Bending", "mode10"],
                ["M2Bending", "mode11"],
                ["M2Bending", "mode12"],
                ["M2Bending", "mode13"],
                ["M2Bending", "mode14"],
                ["M2Bending", "mode15"],
                ["M2Bending", "mode16"],
                ["M2Bending", "mode17"],
                ["M2Bending", "mode18"],
                ["M2Bending", "mode19"],
                ["M2Bending", "mode20"],
            ],
        )

    def getPenality(self):
        """Get the penality of subsystems.

        Returns
        -------
        dict
            Penality of subsystems.
        """

        penality = {}
        penality["M1M3Act"] = float(
            self._configOptCtrlFile.getSetting("m1M3ActuatorPenalty")
        )
        penality["M2Act"] = float(
            self._configOptCtrlFile.getSetting("m2ActuatorPenalty")
        )
        penality["Motion"] = float(self._configOptCtrlFile.getSetting("motionPenalty"))
        return penality

    def getXref(self):
        """Get the X reference.

        Returns
        -------
        str
            X reference.
        """

        return self.xRef
