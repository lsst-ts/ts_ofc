import os
import re
import numpy as np

from lsst.ts.ofc.Utility import InstName, FilterType, DofGroup, \
                                getMatchFilePath, getSetting, \
                                getDirFiles


class OptStateEsti(object):

    def __init__(self):
        """Initialization of optical state estimator class."""

        self.configDir = None
        self.instName = None
        self.configFileName = None
        self.mappingFileName = None
        self.wavelengthTable = None
        self.intrincZkFileName = None
        self.y2CorrectionFileName = None
        self.idxDofFileName = None

        self.strategy = None
        self.zn3Max = None
        self.zn3Idx = None
        self.dofIdx = None
        self.senM = None
        self.matA = None
        self.pinvA = None

    def config(self, configDir, instName=InstName.LSST,
               configFileName="pinv.esti",
               mappingFileName="sensorNameToFieldIdx.txt",
               wavelengthTable="effWaveLength.txt",
               intrincZkFileName="intrinsic_zn",
               y2CorrectionFileName="y2.txt",
               idxDofFileName="idxDOF.txt"):
        """Do the configuration of optical state estimator.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        instName : enum 'InstName', optional
            Instrument name. (the default is InstName.LSST.)
        configFileName : str, optional
            Name of configuration file. (the default is "pinv.esti", which
            uses the pseudo-inverse algorithm.)
        mappingFileName : str, optional
            File name of mapping abbreviated sensor name to index of optical
            field.  (the default is "sensorNameToFieldIdx.txt".)
        wavelengthTable : str, optional
            File name of effective wavelength for each filter in um. (the
            default is "effWaveLength.txt".)
        intrincZkFileName : str, optional
            Intric Zk file name. (the default is "intrinsic_zn".)
        y2CorrectionFileName : str, optional
            y2 correction file name. (the default is "y2.txt".)
        idxDofFileName : str, optional
            Index of DOF file name. (the default is "idxDOF.txt".)
        """

        # Assign the attributes
        self.configDir = configDir
        self.instName = instName
        self.configFileName = configFileName
        self.mappingFileName = mappingFileName
        self.wavelengthTable = wavelengthTable
        self.intrincZkFileName = intrincZkFileName
        self.y2CorrectionFileName = y2CorrectionFileName
        self.idxDofFileName = idxDofFileName

        # Read the setting file
        self._readSetting()

        # Set the sensitivity matrix M
        self._setSenM()

    def _readSetting(self):
        """Read the configuration setting file of optical state estimator."""

        filePath = os.path.join(self.configDir, self.configFileName)
        arrayParamList = ["izn3", "icomp"]

        # Assign the strategy to estimate the optical state
        # from the wavefront error.
        self.strategy = getSetting(filePath, "estimator_strategy",
                                   arrayParamList)

        # Get the number of z3 - zn
        self.zn3Max = getSetting(filePath, "znmax", arrayParamList)
        self.zn3Max = int(self.zn3Max)-3

        # Get the index array of z3-zn
        self.zn3Idx = getSetting(filePath, "izn3", arrayParamList)
        self.zn3Idx = self._getNonZeroIdxFronStrArray(self.zn3Idx)

        # Get the index array of DOF
        self.dofIdx = getSetting(filePath, "icomp", arrayParamList)
        self.dofIdx = self._getNonZeroIdxFronStrArray(self.dofIdx)

    def _getNonZeroIdxFronStrArray(self, strArray):
        """Get the non-zero index array from the string array.

        Parameters
        ----------
        strArray : str
            String array.

        Returns
        -------
        numpy.ndarray
            Non-zero index array.
        """

        array = np.array(strArray.split(), dtype=int)

        return self._getNonZeroIdx(array)

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

    def _setSenM(self):
        """Set the sensitivity matrix M from file with the assigned index
        arrays of Zk and DOF."""

        # Get the sensitivity matrix M file path
        filePath = self._getSenMfilePath(reMatchStr="\AsenM\S+")

        # Get the shape of sensitivity matrix M
        fileName = os.path.basename(filePath)
        shape = self._getSenMshape(fileName)

        # Set the sensitivity matrix M
        self.senM = np.loadtxt(filePath)
        self.senM = self.senM.reshape(shape)
        self.senM = self.senM[np.ix_(np.arange(shape[0]),
                                     self.zn3Idx, self.dofIdx)]

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

        filePaths = getDirFiles(self._getInstDir())
        senMFilePath = getMatchFilePath(reMatchStr, filePaths)

        return senMFilePath

    def _getInstDir(self):
        """Get the instrument directory.

        Returns
        -------
        str
            Instrument directory.
        """

        return os.path.join(self.configDir, self.instName.name.lower())

    def _getSenMshape(self, senMFileName):
        """Get the shape of sensitivity matrix M.

        Parameters
        ----------
        senMFileName : str
            Sensitivity matrix M file name.

        Returns
        -------
        tuple
            Shape of sensitivity matrix M.

        Raises
        ------
        RuntimeError
            Cannot match the shape of M.
        """

        shape = None

        m = re.match(r"\S+_(\d+)_(\d+)_(\d+)\S+", senMFileName)
        if (m is not None):
            shape = m.groups()
            shape = tuple(map(int, shape))

        if shape is None:
            raise RuntimeError("Cannot match the shape of M.")

        return shape

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

    def getSenM(self):
        """Get the sensitivity matrix M.

        The arrangement of M is (field #, zn #, dof #).

        Returns
        -------
        numpy.ndarray
            Sensitivity matrix M.
        """

        return self.senM

    def setAandPinvA(self, fieldIdx, rcond=1e-4):
        """Set the sensitivity matrix A and the related pseudo-inverse
        A^(-1).

        Parameters
        ----------
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.
        rcond : float, optional
            Cutoff for small singular values. (the default is 1e-4.)
        """

        self._setSenA(fieldIdx)
        self._setPinvA(rcond)

    def _setSenA(self, fieldIdx):
        """Set the sensitivity matrix A based on the array of field index.

        Parameters
        ----------
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        Raises
        ------
        RuntimeError
            Equation number < variable number.
        """

        # Constuct the sensitivity matrix A
        self.matA = self.senM[fieldIdx, :, :]
        self.matA = self.matA.reshape((-1, self.senM.shape[2]))

        # Check the dimension of pinv A
        numOfZkEq, numOfDof = self.matA.shape
        if (numOfZkEq < numOfDof):
            raise RuntimeError("Equation number < variable number.")

    def _setPinvA(self, rcond):
        """Set the pueudo-inversed matrix A with the truncation.

        Parameters
        ----------
        rcond : float
            Cutoff for small singular values.
        """

        self.pinvA = np.linalg.pinv(self.matA, rcond=rcond)

    def getSenA(self):
        """Get the sensitivity matrix A.

        Returns
        -------
        numpy.ndarray
            Sensitivity matrix A.
        """

        return self.matA

    def getPinvA(self):
        """Get the pseudo-inversed matrix A.

        Returns
        -------
        numpy.ndarray
            Pseudo-inversed matrix A.
        """

        return self.pinvA

    def getFieldIdx(self, sensorNameArray):
        """Get the array of field index based on the abbreviated sensor
        name (e.g. R22_S11) and mapping file.

        Parameters
        ----------
        sensorNameArray : list
            Array of abbreviated sensor name.

        Returns
        -------
        list
            Field index array.
        """

        filePath = os.path.join(self._getInstDir(), self.mappingFileName)

        fieldIdx = []
        for sensorName in sensorNameArray:
            field = getSetting(filePath, sensorName)
            fieldIdx.append(int(field))

        return fieldIdx

    def getEffWave(self, filterType):
        """Get the effective wavelength in um.

        This is based on the active filter type (U, G, R, I, Z, Y, REF). It
        is noted that "ref" means the monochromatic reference wavelength.

        Parameters
        ----------
        filterType : enum 'FilterType'
            Active filter type.

        Returns
        -------
        float
            Effective wavelength in um.
        """

        filePath = os.path.join(self.configDir, self.wavelengthTable)
        param = filterType.name.lower()
        effWave = float(getSetting(filePath, param))

        return effWave

    def getY2Corr(self, fieldIdx, isNby1Array=False):
        """Get the y2 correction array. This is the zk offset between the
        camera center and corner.

        Parameters
        ----------
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        isNby1Array : bool, optional
            In the format of nx1 array or not. (the default is False.)

        Returns
        -------
        numpy.ndarray
            y2 correction array.
        """

        filePath = os.path.join(self._getInstDir(),
                                self.y2CorrectionFileName)
        y2c = np.loadtxt(filePath)
        y2c = y2c[np.ix_(fieldIdx, self.zn3Idx)]

        if (isNby1Array):
            y2c = y2c.reshape(-1, 1)

        return y2c

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
        """

        # Assign the parameter name
        dofVal = dofGroup.value
        if (dofVal == 1):
            param = "M2_Hex_Pos"
        elif (dofVal == 2):
            param = "Cam_Hex_Pos"
        elif (dofVal == 3):
            param = "M1M3_Bend"
        elif (dofVal == 4):
            param = "M2_Bend"

        # Get the values from the file
        filePath = os.path.join(self.configDir, self.idxDofFileName)
        startIdx, groupLeng = getSetting(filePath, param)

        # Change the data type
        startIdx = int(startIdx)
        groupLeng = int(groupLeng)

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

        # Assign the index arrays
        self.zn3Idx = np.array(zn3Idx, dtype=int)
        self.dofIdx = np.array(dofIdx, dtype=int)

        # Reset the sensitivity matrix M
        self._setSenM()

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

        if (len(zkToUse) != self.zn3Max):
            raise RuntimeError("The length of 'zkToUse' should be %d."
                               % self.zn3Max)

        # Get the index of zk to use
        zn3Idx = self._getNonZeroIdx(zkToUse)

        # Assign the order for the following iteration
        dofInputs = [m2HexPos, camHexPos, m1m3Bend, m2Bend]

        dofIdx = np.array([], dtype=int)
        for dofInput, dofGroup in zip(dofInputs, DofGroup):
            startIdx, groupLeng = self.getGroupIdxAndLeng(dofGroup)

            if (len(dofInput) != groupLeng):
                raise RuntimeError("The length of DOF is incorrect.")

            idx = self._getNonZeroIdx(dofInput)
            dofIdx = np.append(dofIdx, idx+startIdx)

        self.setZkAndDofIdxArrays(zn3Idx, dofIdx)

    def getWfAndFieldIdFromFile(self, wfFilePath, sensorNameArray):
        """Get the wavefront error and field Id from the file.

        Parameters
        ----------
        wfFilePath : str
            Wavefront error file path.
        sensorNameArray : list
            List of abbreviated sensor name.

        Returns
        -------
        numpy.ndarray
            Wavefront error.
        list
            Field index array.

        Raises
        ------
        RuntimeError
            Number of sensors does not match the file.
        """

        wfErr = np.loadtxt(wfFilePath)
        fieldIdx = self.getFieldIdx(sensorNameArray)

        if (len(fieldIdx) != wfErr.shape[0]):
            raise RuntimeError("Number of sensors does not match the file.")

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

    def estiOptState(self, filterType, wfErr, fieldIdx):
        """Estimate the optical state in the basis of degree of
        freedom (DOF).

        Parameters
        ----------
        filterType : enum 'FilterType'
            Active filter type.
        wfErr : numpy.ndarray
            Wavefront error im um.
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        Returns
        -------
        numpy.ndarray
            Optical state in the basis of DOF.
        """

        wfErr = wfErr[:, self.zn3Idx].reshape(-1, 1)
        intrinsicZk = self._getIntrinsicZk(filterType, fieldIdx)
        y2c = self.getY2Corr(fieldIdx, isNby1Array=True)

        # Solve y = A*x by x = pinv(A)*y
        y = wfErr - intrinsicZk - y2c
        x = self.pinvA.dot(y)

        return x.ravel()

    def _getIntrinsicZk(self, filterType, fieldIdx):
        """Get the intrinsic zk of specific filter based on the array of
        field index. The output array shape is nx1.

        Parameters
        ----------
        filterType : enum 'FilterType'
            Active filter type.
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        Returns
        -------
        numpy.ndarray
            Instrinsic Zk of specific effective wavelength in um.
        """

        # Get the intrinsicZk file path
        reMatchStrTail = ""
        if (filterType != FilterType.REF):
            reMatchStrTail = "_" + filterType.name

        reMatchStr = "\A" + self.intrincZkFileName + reMatchStrTail + ".\S+"
        filePaths = getDirFiles(self._getInstDir())
        zkFilePath = getMatchFilePath(reMatchStr, filePaths)

        # Remap the zk index for z0-z2
        zkIdx = self.zn3Idx + 3

        # Get the intrinsicZk with the consideration of effective wavelength
        intrinsicZk = np.loadtxt(zkFilePath)
        intrinsicZk = intrinsicZk[np.ix_(fieldIdx, zkIdx)]
        intrinsicZk = intrinsicZk*self.getEffWave(filterType)
        intrinsicZk = intrinsicZk.reshape(-1, 1)

        return intrinsicZk


if __name__ == "__main__":
    pass
