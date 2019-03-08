import os
import numpy as np

from lsst.ts.ofc.Utility import InstName, DofGroup, getMatchFilePath, \
    getDirFiles
from lsst.ts.ofc.ParamReaderYaml import ParamReaderYaml


class DataShare(object):

    def __init__(self):
        """Initialization of data share class."""

        self.configDir = ""
        self.instName = InstName.LSST

        self.zn3Idx = np.array([], dtype=int)
        self.dofIdx = np.array([], dtype=int)

        self._zkAndDofIdxArraySetFile = ParamReaderYaml()
        self._senMfile = ParamReaderYaml()
        self._mappingFile = ParamReaderYaml()
        self._idxDofFile = ParamReaderYaml()
        self._sensorNameToIdFile = ParamReaderYaml()

    def config(self, configDir, instName=InstName.LSST,
               zkAndDofIdxArraySetFileName="zkAndDofIdxArraySet.yaml",
               mappingFileName="sensorNameToFieldIdx.yaml",
               idxDofFileName="idxDOF.yaml",
               sensorNameToIdFileName="sensorNameToId.yaml"):
        """Do the configuration of DataShare class.

        zk: Annular Zernike polynomial.
        DOF: Degree of Freedom.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        instName : enum 'InstName', optional
            Instrument name. (the default is InstName.LSST.)
        zkAndDofIdxArraySetFileName : str, optional
            File name of zk and DOF index array set. (the default is
            "zkAndDofIdxArraySet.yaml".)
        mappingFileName : str, optional
            File name of mapping abbreviated sensor name to index of optical
            field.  (the default is "sensorNameToFieldIdx.yaml".)
        idxDofFileName : str, optional
            Index of DOF file name. (the default is "idxDOF.yaml".)
        sensorNameToIdFileName : str, optional
            Configuration file name to map sensor Id to name. (the default
            is "sensorNameToId.yaml".)
        """

        self.configDir = configDir
        self.instName = instName

        zkAndDofIdxArraySetFilePath = os.path.join(configDir,
                                                   zkAndDofIdxArraySetFileName)
        self._zkAndDofIdxArraySetFile.setFilePath(zkAndDofIdxArraySetFilePath)

        mappingFilePath = os.path.join(self.getInstDir(), mappingFileName)
        self._mappingFile.setFilePath(mappingFilePath)

        idxDofFilePath = os.path.join(configDir, idxDofFileName)
        self._idxDofFile.setFilePath(idxDofFilePath)

        sensorNameToIdFilePath = os.path.join(configDir,
                                              sensorNameToIdFileName)
        self._sensorNameToIdFile.setFilePath(sensorNameToIdFilePath)

        senMfilePath = self._getSenMfilePath(reMatchStr=r"\AsenM\S+")
        self._senMfile.setFilePath(senMfilePath)

        self._readZn3AndDofIdxArray()

    def _readZn3AndDofIdxArray(self):
        """Read the Z3-Zn and DOF index arrays.

        DOF: degree of freedom.
        """

        # Get the zn (z3-z22) index
        zn3IdxList = self._zkAndDofIdxArraySetFile.getSetting("zn3Idx")
        self.zn3Idx = self._getNonZeroIdx(zn3IdxList)

        # Get the DOF index
        dofIdxDict = self._zkAndDofIdxArraySetFile.getSetting("dofIdx")

        # Get the dof index as an array from the dictionary values
        dofIdxArray = self._appendDictValuesToArray(dofIdxDict)
        self.dofIdx = self._getNonZeroIdx(dofIdxArray)

    def _appendDictValuesToArray(self, aDict):
        """Append the dictionary values to array.

        Parameters
        ----------
        aDict : dict
            A dictionary instance.

        Returns
        -------
        numpy.ndarray
            Values in array.
        """

        array = np.array([])
        for value in aDict.values():
            array = np.append(array, value)

        return array

    def _getNonZeroIdx(self, array):
        """Get the non-zero index array.

        Parameters
        ----------
        array : numpy.ndarray or list
            Array to look for the non-zero index.

        Returns
        -------
        numpy.ndarray
            Non-zero index array.
        """

        return np.where(np.array(array) != 0)[0]

    def _getSenMfilePath(self, reMatchStr):
        """Get the sensitivity matrix M file path.

        Parameters
        ----------
        reMatchStr : str
            Matching string for the regular expression.

        Returns
        -------
        str
            Sensitivity matrix M file path.
        """

        filePaths = getDirFiles(self.getInstDir())
        senMFilePath = getMatchFilePath(reMatchStr, filePaths)

        return senMFilePath

    def getInstDir(self):
        """Get the instrument directory.

        Returns
        -------
        str
            Instrument directory.
        """

        return os.path.join(self.configDir, self.instName.name.lower())

    def getConfigDir(self):
        """Get the configuration directory.

        Returns
        -------
        str
            configuration directory.
        """

        return self.configDir

    def getSenM(self):
        """Get the sensitivity matrix M.

        The arrangement of M is (field #, zn #, dof #).

        Returns
        -------
        numpy.ndarray
            Sensitivity matrix M.
        """

        # Set the sensitivity matrix M
        senM = self._senMfile.getMatContent()
        senM = senM[np.ix_(np.arange(senM.shape[0]), self.zn3Idx, self.dofIdx)]

        return senM

    def getDofIdx(self):
        """Get the index array of degree of freedom (DOF).

        Returns
        -------
        numpy.ndarray
            Index array of DOF.
        """

        return self.dofIdx

    def getZn3Idx(self):
        """Get the index array of z3 to zn.

        Returns
        -------
        numpy.ndarray
            Index array of z3 to zn.
        """

        return self.zn3Idx

    def getFieldIdx(self, sensorNameList):
        """Get the list of field index based on the abbreviated sensor
        name (e.g. R22_S11) and mapping file.

        Parameters
        ----------
        sensorNameList : list[str]
            List of abbreviated sensor name.

        Returns
        -------
        list[int]
            Field index array.

        Raises
        ------
        TypeError
            The input type is not list.
        """

        fieldIdx = []
        if (self._inputIsList(sensorNameList)):
            for sensorName in sensorNameList:
                field = self._mappingFile.getSetting(sensorName)
                fieldIdx.append(int(field))

        return fieldIdx

    def _inputIsList(self, input):
        """Check the type of input is list or not.

        Parameters
        ----------
        input : obj
            Input.

        Returns
        -------
        bool
            True if the input's type is list.

        Raises
        ------
        TypeError
            The input type is not list.
        """

        inputIsList = True
        if (not isinstance(input, list)):
            inputIsList = False
            raise TypeError("The input type is '%s' instead of list."
                            % type(input))

        return inputIsList

    def getGroupIdxAndLeng(self, dofGroup):
        """Get the start index and length of specific group of degree of
        freedom (DOF).

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group.

        Returns
        -------
        int
            Start index of group.
        int
            Index length of group.

        Raises
        ------
        ValueError
            The input is not found in the idxDof file.
        """

        # Assign the parameter name
        if (dofGroup == DofGroup.M2HexPos):
            param = "m2HexPos"
        elif (dofGroup == DofGroup.CamHexPos):
            param = "camHexPos"
        elif (dofGroup == DofGroup.M1M3Bend):
            param = "m1M3Bend"
        elif (dofGroup == DofGroup.M2Bend):
            param = "m2Bend"
        else:
            raise ValueError("'%s' is not found in the '%s'."
                             % (dofGroup, self._idxDofFile.getFilePath()))

        # Get the values from the file
        groupInfo = self._idxDofFile.getSetting(param)
        startIdx = int(groupInfo["startIdx"])
        groupLeng = int(groupInfo["idxLength"])

        return startIdx, groupLeng

    def setZkAndDofIdxArrays(self, zn3Idx, dofIdx):
        """Set the index array of zn and degree of freedom (DOF).

        Parameters
        ----------
        zn3Idx : numpy.ndarray[int] or list[int]
            Index array of z3 to zn.
        dofIdx : numpy.ndarray[int] or list[int]
            Index array of DOF.
        """

        self.zn3Idx = np.array(zn3Idx, dtype=int)
        self.dofIdx = np.array(dofIdx, dtype=int)

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

        Raises
        ------
        ValueError
            The length of 'zkToUse' is incorrect.
        ValueError
            "The length of DOF is incorrect."
        """

        zn3Max = self._getZn3Max()
        if (len(zkToUse) != zn3Max):
            raise ValueError("The length of 'zkToUse' should be %d."
                             % zn3Max)

        # Get the index of zk to use
        zn3Idx = self._getNonZeroIdx(zkToUse)

        # Assign the order for the following iteration with zip
        dofInputs = [m2HexPos, camHexPos, m1m3Bend, m2Bend]

        dofIdx = np.array([], dtype=int)
        for dofInput, dofGroup in zip(dofInputs, DofGroup):
            startIdx, groupLeng = self.getGroupIdxAndLeng(dofGroup)

            if (len(dofInput) != groupLeng):
                raise ValueError("The length of DOF is incorrect.")

            idx = self._getNonZeroIdx(dofInput)
            dofIdx = np.append(dofIdx, idx+startIdx)

        self.setZkAndDofIdxArrays(zn3Idx, dofIdx)

    def _getZn3Max(self):
        """Get the number of terms of Z3 to Zn.

        Zn: Annular Zernike polynomial.

        Returns
        -------
        int
            Number of terms of Z3 to Zn.
        """

        zn3Max = self._zkAndDofIdxArraySetFile.getSetting("znmax")
        zn3Max = int(zn3Max)-3

        return zn3Max

    def getWfAndFieldIdFromFile(self, wfFilePath, sensorNameList):
        """Get the wavefront error and field Id from the file.

        Parameters
        ----------
        wfFilePath : str
            Wavefront error file path.
        sensorNameList : list[str]
            List of abbreviated sensor name.

        Returns
        -------
        numpy.ndarray
            Wavefront error.
        list
            Field index list.

        Raises
        ------
        ValueError
            Number of sensors does not match the file.
        """

        wfErr = np.loadtxt(wfFilePath)
        fieldIdx = self.getFieldIdx(sensorNameList)

        if (len(fieldIdx) != wfErr.shape[0]):
            raise ValueError("Number of sensors does not match the file.")

        return wfErr, fieldIdx

    def getWfAndFieldIdFromShwfsFile(self, wfFilePath, sensorName="R22_S11"):
        """Get the wavefront error and field Id from the SHWFS file.

        SHWFS: Shack-Hartmann wavefront sensor.

        Parameters
        ----------
        wfFilePath : str
            Wavefront error file path.
        sensorName : str, optional
            Sensor name. (the default is "R22_S11", which uses the central
            position of main camera. This is to get the sensitivity matrix.)

        Returns
        -------
        numpy.ndarray
            Wavefront error.
        list
            Field index array.
        """

        # Only z3 to zn is considered
        wfErr = np.loadtxt(wfFilePath, usecols=1)[3:]
        fieldIdx = self.getFieldIdx([sensorName])

        return wfErr, fieldIdx

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

        sensorNameList = []
        if (self._inputIsList(sensorIdList)):
            content = self._sensorNameToIdFile.getContent()
            for sensorId in sensorIdList:
                try:
                    sensorName = self._getKeyFromValueInDict(content, sensorId)
                    sensorNameList.append(sensorName)
                except ValueError:
                    pass

        return sensorNameList, len(sensorNameList)

    def _getKeyFromValueInDict(self, aDict, value):
        """Get the key from value in a dictionary object.

        Parameters
        ----------
        aDict : dict
            Dictionary object.
        value : str or int
            Value in the dictionary.

        Returns
        -------
        str
            Dictionary key.
        """

        return list(aDict.keys())[list(aDict.values()).index(value)]

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

        sensorIdList = []
        if (self._inputIsList(sensorNameList)):
            for sensorName in sensorNameList:
                sensorId = self._sensorNameToIdFile.getSetting(sensorName)
                sensorIdList.append(sensorId)

        return sensorIdList


if __name__ == "__main__":
    pass
