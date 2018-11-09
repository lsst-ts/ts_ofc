import os
import numpy as np

from lsst.ts.ofc.Utility import getSetting, DofGroup


class ZTAAC(object):

    def __init__(self, optStateEsti, optCtrl, dataShare):
        """Initialization of Zernike to actuator adjustment calculator
        (ZTAAC) class.

        Parameters
        ----------
        optStateEsti : OptStateEsti
            Configurated optical state estimator instance.
        optCtrl : OptCtrl
            Configurated optimal control instance.
        dataShare : DataShare
            Instance of DataShare class or related decorated class.
        """

        self.optStateEsti = optStateEsti
        self.optCtrl = optCtrl
        self.dataShare = dataShare

        self.filterType = None
        self.defaultGain = None
        self.fwhmThresholdInArcsec = None

    def config(self, filterType=None, defaultGain=0.7,
               fwhmThresholdInArcsec=0.2):
        """Do the configuration of Zernike to actuator adjustment calculator
        (ZTAAC).

        This is a high-level class to use the "optical state estimator" and
        "optimal control".

        Parameters
        ----------
        filterType : enum 'FilterType', optional
            Active filter type. (the default is None.)
        defaultGain : float, optional
            Default gain value in the feedback. It should be in the range of 0
            and 1. (the default is 0.7.)
        fwhmThresholdInArcsec : float, optional
            Full width at half maximum (FWHM) threshold in arcsec. (the
            default is 0.2.)
        """

        self.filterType = filterType
        self.defaultGain = defaultGain
        self.fwhmThresholdInArcsec = fwhmThresholdInArcsec

    def mapSensorIdToName(self, sensorIdList):
        """Map the list of sensor Id to sensor name.

        If no sensor name is found for a specific Id, there will be no returned
        value.

        Parameters
        ----------
        sensorIdList : list[int]
            List of sensor Id.

        Returns
        -------
        list
            List of abbreviated sensor names.
        int
            Number of sensors.
        """

        return self.dataShare.mapSensorIdToName(sensorIdList)

    def mapSensorNameToId(self, sensorNameList):
        """Map the array of sensor name to sensor Id.

        Parameters
        ----------
        sensorNameList : list[str]
            List of abbreviated sensor names.

        Returns
        -------
        list[int]
            List of sensor Id.
        """

        return self.dataShare.mapSensorNameToId(sensorNameList)

    def setFilter(self, filterType):
        """Set the active filter type.

        Parameters
        ----------
        filterType : enum 'FilterType'
            Active filter type.
        """

        self.filterType = filterType

    def getFilter(self):
        """Get the active filter type.

        Returns
        -------
        enum 'FilterType'
            Active filter type.
        """

        return self.filterType

    def setState0(self, state0InDof):
        """Set the state 0 in degree of freedom (DOF).

        Parameters
        ----------
        state0InDof : numpy.ndarray or list
            State 0 in DOF.
        """

        self.optCtrl.setState0(state0InDof)

    def getState0(self):
        """Get the state 0 in degree of freedom (DOF).

        Returns
        -------
        numpy.ndarray
            State 0 in DOF.
        """

        numOfState0 = self.optCtrl.getNumOfState0()
        dofIdx = np.arange(numOfState0)

        return self.optCtrl.getState0(dofIdx)

    def setStateToState0(self):
        """Set the state to state 0."""

        self.optCtrl.initStateToState0()

    def setState0FromFile(self, state0InDofFileName="state0inDof.txt"):
        """Set the state 0 in degree of freedom (DOF) from the file.

        Parameters
        ----------
        state0InDofFileName : str, optional
            File name to read the telescope state 0, which depends on the
            instrument. (the default is "state0inDof.txt".)
        """

        state0InDof = self.dataShare.getState0FromFile(state0InDofFileName=state0InDofFileName)
        self.setState0(state0InDof)

    def setGain(self, gain):
        """Set the gain value.

        Parameters
        ----------
        gain : float
            Gain value in the feedback. It should be in the range of 0 and 1.
        """

        self.optCtrl.setGain(gain)

    def setGainByPSSN(self, pssn, sensorNameList, eta=1.086, fwhmAtm=0.6):
        """Set the gain value based on PSSN.

        PSSN: Normalized point spread function.

        Parameters
        ----------
        pssn : numpy.ndarray or list
            PSSN.
        sensorNameList : list[str]
            List of abbreviated sensor names.
        eta : float, optional
            Eta in FWHM calculation. (the default is 1.086.)
        fwhmAtm : float, optional
            FWHM in atmosphere. (the default is 0.6.)
        """

        fieldIdx = self.dataShare.getFieldIdx(sensorNameList)
        fwhmGq = self.optCtrl.calcEffGQFWHM(self.dataShare, pssn, fieldIdx)

        if (fwhmGq > self.fwhmThresholdInArcsec):
            gainToUse = 1
        else:
            gainToUse = self.defaultGain

        self.setGain(gainToUse)

    def getGainInUse(self):
        """Get the gain value used in the Optimal Control.

        It is noted that the gain value in use might be different from
        the default gain value if the image quality is bad (Gain = 1).

        Returns
        -------
        float
            Gain value.
        """

        return self.optCtrl.getGain()

    def getWfFromFile(self, wfFilePath,
                      sensorNameList=["R44_S00", "R04_S20", "R00_S22",
                                      "R40_S02"]):
        """Get the wavefront error from the file.

        Parameters
        ----------
        wfFilePath : str
            Wavefront error file path.
        sensorNameList : list[str], optional
            List of abbreviated sensor names. (the default is ["R44_S00",
            "R04_S20", "R00_S22", "R40_S02"].)

        Returns
        -------
        numpy.ndarray
            Wavefront error.
        """

        wfErr = self.dataShare.getWfAndFieldIdFromFile(wfFilePath,
                                                       sensorNameList)[0]
        return wfErr

    def getWfFromShwfsFile(self, wfFilePath):
        """Get the wavefront error from the SHWFS file.

        SHWFS: Shack-Hartmann wavefront sensor.

        Parameters
        ----------
        wfFilePath : str
            Wavefront error file path.

        Returns
        -------
        numpy.ndarray
            Wavefront error.
        str
            Sensor name used in the sensitivity matrix.
        """

        sensorName = "R22_S11"
        wfErr = self.dataShare.getWfAndFieldIdFromShwfsFile(
                            wfFilePath, sensorName=sensorName)[0]

        return wfErr, sensorName

    def estiUkWithGain(self, wfErr, sensorNameList):
        """Estimate uk with gain compensation.

        Parameters
        ----------
        wfErr : numpy.ndarray
            Wavefront error.
        sensorNameList : list[str]
            List of abbreviated sensor names.

        Returns
        -------
        numpy.ndarray
            Calculated uk in the basis of degree of freedom (DOF).
        """

        fieldIdx = self.dataShare.getFieldIdx(sensorNameList)
        optSt = self.optStateEsti.estiOptState(self.dataShare, self.filterType,
                                               wfErr, fieldIdx)
        uk = self.optCtrl.estiUkWithGain(self.dataShare, self.filterType, optSt)

        return uk

    def aggState(self, calcDof):
        """Aggregate the calculated degree of freedom (DOF) in the state.

        Parameters
        ----------
        calcDof : numpy.ndarray
            Calculated DOF.
        """

        dofIdx = self.dataShare.getDofIdx()
        self.optCtrl.aggState(calcDof, dofIdx)

    def getGroupDof(self, dofGroup, inputDof=None):
        """Get the degree of freedom (DOF) of specific group.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.
        inputDof : numpy.ndarray or list, optional
            Input DOF. (the default is None.)

        Returns
        -------
        numpy.ndarray
            DOF.
        """

        startIdx, groupLeng = self.dataShare.getGroupIdxAndLeng(dofGroup)
        dof = self.optCtrl.getGroupDof(startIdx, groupLeng, inputDof=inputDof)

        return dof

    def setZkAndDofInGroups(self, zkToUse=np.ones(19, dtype=int),
                            m2HexPos=np.ones(5, dtype=int),
                            camHexPos=np.ones(5, dtype=int),
                            m1m3Bend=np.ones(20, dtype=int),
                            m2Bend=np.ones(20, dtype=int)):
        """Set the index array of Zk and DOF in groups (M2 hexapod,
        camera hexapod, M1M3 bending mode, and M2 bending mode).

        For the element in input index array, use 1 for True and 0 for
        False. For example, if the m2HexPos is [1, 1, 1, 0, 0], only the
        first three positions will be used.

        Parameters
        ----------
        zkToUse : numpy.ndarray[int] or list[int], optional
            z3 to zn. (the default is np.ones(19, dtype=int))
        m2HexPos : numpy.ndarray[int] or list[int], optional
            M2 hexapod position. (the default is np.ones(5, dtype=int))
        camHexPos : numpy.ndarray[int] or list[int], optional
            Camera hexapod position. (the default is np.ones(5, dtype=int))
        m1m3Bend : numpy.ndarray[int] or list[int], optional
            M1M3 bending mode. (the default is np.ones(20, dtype=int))
        m2Bend : numpy.ndarray[int] or list[int], optional
            M2 bending mode. (the default is np.ones(20, dtype=int))
        """

        self.dataShare.setZkAndDofInGroups(zkToUse=zkToUse,
                                           m2HexPos=m2HexPos,
                                           camHexPos=camHexPos,
                                           m1m3Bend=m1m3Bend,
                                           m2Bend=m2Bend)

    def rotUk(self, camRot, uk):
        """Rotate uk based on the camera rotation angle.

        Parameters
        ----------
        camRot : CamRot
            Instance of camera rotation class.
        uk : numpy.ndarray
            Calculated uk in the basis of degree of freedom (DOF).

        Returns
        -------
        numpy.ndarray
            Rotated uk.

        Raises
        ------
        ValueError
            Order of DofGroup and DOF are different.
        """

        dof = self._transUkToDof(uk)
        dofOrder = [DofGroup.M2HexPos, DofGroup.CamHexPos, DofGroup.M1M3Bend,
                    DofGroup.M2Bend]

        rotDof = []
        for dofGroup, dofItemInOrder in zip(DofGroup, dofOrder):
            if (dofGroup != dofItemInOrder):
                raise ValueError("Order of DofGroup and DOF are different.")

            dofOfGroup = self.getGroupDof(dofGroup, inputDof=dof)
            tiltXYinArcsec = self._getTiltXY(dofGroup)
            rotDofOfGroup = camRot.rotGroupDof(dofGroup, dofOfGroup,
                                               tiltXYinArcsec=tiltXYinArcsec)
            rotDof = np.append(rotDof, rotDofOfGroup)

        rotUk = self._transDofToUk(rotDof)

        return rotUk

    def _transDofToUk(self, dof):
        """Transform the degree of freedom (DOF) to uk based on the index array
        of DOF.

        Parameters
        ----------
        dof : numpy.ndarray
            DOF.

        Returns
        -------
        numpy.ndarray
            Calculated uk in the basis of DOF.
        """

        dofIdx = self.dataShare.getDofIdx()

        return dof[dofIdx]

    def _transUkToDof(self, uk):
        """Transform uk to the degree of freedom (DOF) based on the index array
        of DOF.

        Parameters
        ----------
        uk : numpy.ndarray
            Calculated uk in the basis of DOF.

        Returns
        -------
        numpy.ndarray
            DOF.
        """

        dof = np.zeros(self.optCtrl.getNumOfState0())
        dofIdx = self.dataShare.getDofIdx()
        dof[dofIdx] = uk

        return dof

    def _getTiltXY(self, dofGroup):
        """Get the relative tilt angle XY in arcsec compared with the camera
        hexapod.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            Degree of freedom (DOF) group.

        Returns
        -------
        tuple
            Tilt angle (x, y) in arcsec.
        """

        dofIdx = np.arange(self.optCtrl.getNumOfState0())
        stateInDof = self.optCtrl.getState(dofIdx)
        m2PosRx = stateInDof[3]
        m2PosRy = stateInDof[4]
        camPosRx = stateInDof[8]
        camPosRy = stateInDof[9]

        if dofGroup in (DofGroup.M2HexPos, DofGroup.M2Bend):
            tiltXYinArcsec = (m2PosRx-camPosRx, m2PosRy-camPosRy)
        elif (dofGroup == DofGroup.CamHexPos):
            tiltXYinArcsec = (0, 0)
        elif (dofGroup == DofGroup.M1M3Bend):
            tiltXYinArcsec = (camPosRx, camPosRy)

        return tiltXYinArcsec


if __name__ == "__main__":
    pass
