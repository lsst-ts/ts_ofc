import os
import numpy as np

from lsst.ts.ofc.OptStateEsti import InstName, FilterType, getSetting, DofGroup
from lsst.ts.ofc.OptStateEsti import OptStateEsti
from lsst.ts.ofc.OptCtrl import OptCtrl

class ZTAAC(object):

    def __init__(self, optStateEsti, optCtrl):
        """Initialization of Zernike to actuator adjustment calculator
        (ZTAAC) class.

        Parameters
        ----------
        optStateEsti : OptStateEsti
            Configurated optical state estimator instance.
        optCtrl : OptCtrl
            Configurated optimal control instance.
        """

        self.optStateEsti = optStateEsti
        self.optCtrl = optCtrl        
        
        self.configDir = None
        self.sensorIdToNameFileName = None
        self.filterType = None
        self.rcond = None
        self.defaultGain = None
        self.fwhmThresholdInArcsec = None

    def config(self, configDir, sensorIdToNameFileName="sensorIdToName.txt",
               filterType=None, rcond=1e-4, defaultGain=0.7,
               fwhmThresholdInArcsec=0.2):
        """Do the configuration of Zernike to actuator adjustment calculator
        (ZTAAC).

        This is a high-level class to use the "optical state estimator" and
        "optimal control".

        Parameters
        ----------
        configDir : str
            Configuration directory.
        sensorIdToNameFileName : str, optional
            Configuration file name to map sensor Id to name. (the default
            is "sensorIdToName.txt".)
        filterType : enum 'FilterType', optional
            Active filter type. (the default is None.)
        rcond : float, optional
            Cutoff for small singular values. (the default is 1e-4.)
        defaultGain : float, optional
            Default gain value in the feedback. It should be in the range of 0
            and 1. (the default is 0.7.)
        fwhmThresholdInArcsec : float, optional
            Full width at half maximum (FWHM) threshold in arcsec. (the
            default is 0.2.)
        """

        self.configDir = configDir
        self.sensorIdToNameFileName = sensorIdToNameFileName
        self.filterType = filterType
        self.rcond = rcond
        self.defaultGain = defaultGain
        self.fwhmThresholdInArcsec = fwhmThresholdInArcsec

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

        filePath = self._getMapSensorIdAndNameFilePath()

        sensorNameList = []
        for sensorId in sensorIdList:
            try:
                sensorNameList.append(getSetting(filePath, str(sensorId)))
            except RuntimeError:
                pass

        return sensorNameList, len(sensorNameList)

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
        
        filePath = self._getMapSensorIdAndNameFilePath()

        sensorIdList = []
        for sensorName in sensorNameList:
            sensorIdList.append(self._mapSensorNameToIdFromFile(filePath,
                                                                sensorName))

        return sensorIdList

    def _getMapSensorIdAndNameFilePath(self):
        """Get the file path that maps the sensor Id and name.

        Returns
        -------
        str
            File path.
        """

        return os.path.join(self.configDir, self.sensorIdToNameFileName)

    def _mapSensorNameToIdFromFile(self, filePath, sensorName):
        """Map the sensor name to Id based on the mapping file.

        Parameters
        ----------
        filePath : str
            File path.
        sensorName : str
            Abbreviated sensor name.
        
        Returns
        -------
        int
            Sensor Id.
        
        Raises
        ------
        ValueError
            Can not find the sensor Id of input sensor name.
        """
        
        sensorId = None
        with open(filePath) as file:
            for line in file:
                line = line.strip()

                # Skip the comment or empty line
                if line.startswith("#") or (len(line) == 0):
                    continue

                sensorIdInFile, sensorNameInFile = line.split()

                if (sensorNameInFile == sensorName):
                    sensorId = int(sensorIdInFile)
                    break

        if (sensorId is None):
            raise ValueError("Can not find the sensor Id of '%s'." % sensorName)

        return sensorId

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

        fieldIdx = self.optStateEsti.getFieldIdx(sensorNameList)
        fwhmGq = self.optCtrl.calcEffGQFWHM(pssn, fieldIdx, eta=eta,
                                            fwhmAtm=fwhmAtm)

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

        wfErr = self.optStateEsti.getWfAndFieldIdFromFile(wfFilePath,
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
        wfErr = self.optStateEsti.getWfAndFieldIdFromShwfsFile(wfFilePath,
                                                    sensorName=sensorName)[0]

        return wfErr, sensorName

    def estiUk(self, wfErr, sensorNameList):
        """Estimate uk.

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

        # Calculate the optical state
        fieldIdx = self.optStateEsti.getFieldIdx(sensorNameList)

        self.optStateEsti.setAandPinvA(fieldIdx, rcond=self.rcond)
        optSt = self.optStateEsti.estiOptState(self.filterType, wfErr,
                                               fieldIdx)

        # Estimate uk
        zn3Idx = self.optStateEsti.zn3Idx
        dofIdx = self.optStateEsti.dofIdx
        effWave = self.optStateEsti.getEffWave(self.filterType)
        senM = self.optStateEsti.senM
        fieldNumInQwgt = self.optCtrl.getNumOfFieldInQwgt()
        y2c = self.optStateEsti.getY2Corr(np.arange(fieldNumInQwgt),                                          isNby1Array=False)

        self.optCtrl.setMatF(zn3Idx, dofIdx, effWave, senM)
        uk = self.optCtrl.estiUk(zn3Idx, dofIdx, effWave, senM, y2c, optSt)

        return uk

    def aggState(self, calcDof):
        """Aggregate the calculated degree of freedom (DOF) in the state.

        Parameters
        ----------
        calcDof : numpy.ndarray
            Calculated DOF.
        """

        dofIdx = self.optStateEsti.dofIdx
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
        
        startIdx, groupLeng = self.optStateEsti.getGroupIdxAndLeng(dofGroup)
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

        self.optStateEsti.setZkAndDofInGroups(zkToUse=zkToUse,
                                              m2HexPos=m2HexPos,
                                              camHexPos=camHexPos,
                                              m1m3Bend=m1m3Bend,
                                              m2Bend=m2Bend)

    def rotUk(self):
        pass

    def _transDofToUk(self):
        pass

    def _transUkToDof(self):
        pass

    def _getTiltXY(self):
        pass


if __name__ == "__main__":
    
    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"

    optStateEsti = OptStateEsti()
    optStateEsti.config(configDir, instName=InstName.LSST)

    optCtrl = OptCtrl()
    optCtrl.config(configDir, instName=InstName.LSST,
                   configFileName="optiPSSN_x00.ctrl")

    ztaac = ZTAAC(optStateEsti, optCtrl)
    ztaac.config(configDir)

    gain = 0.7
    ztaac.setGain(gain)

    # ztaac.setState0(np.random.rand(50))
    # state0 = ztaac.getState0()
    # ztaac.setStateToState0()

    sensorIdList = [1, 2, 3, 4, 5, -1, -1]
    sensorNameList, numOfSensor = ztaac.mapSensorIdToName(sensorIdList)
    sensorIdList = ztaac.mapSensorNameToId(sensorNameList)
    
    pssn = np.ones(31)*0.7
    sensorIdList = [100, 103, 104, 105, 97, 96, 95, 140, 150, 109, 44, 46,
                    93, 180, 120, 118, 18, 45, 82, 183, 122, 116, 24, 40,
                    81, 179, 161, 70, 5, 33, 123]
    sensorNameList, numOfSensor = ztaac.mapSensorIdToName(sensorIdList)

    ztaac.setGainByPSSN(pssn, sensorNameList)

    testDataDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/tests/testData"
    testWfsFile = "lsst_wfs_error_iter0.z4c"
    testWfsFilePath = os.path.join(testDataDir, testWfsFile)

    wfErr = ztaac.getWfFromFile(testWfsFilePath)
    ztaac.setFilter(FilterType.REF)
    sensorNameList = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]

    uk = ztaac.estiUk(wfErr, sensorNameList)
    ztaac.aggState(uk)

    dof = ztaac.getGroupDof(DofGroup.M2HexPos)
    print(dof)

 