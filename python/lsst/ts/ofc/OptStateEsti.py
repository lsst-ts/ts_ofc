import os
import re
import numpy as np

from lsst.ts.ofc.Utility import InstName, getSetting, getDirFiles, getMatchFilePath


class OptStateEsti(object):

    def __init__(self):

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

        self.configDir = configDir
        self.instName = instName
        self.configFileName = configFileName
        self.mappingFileName = mappingFileName
        self.wavelengthTable = wavelengthTable
        self.intrincZkFileName = intrincZkFileName
        self.y2CorrectionFileName = y2CorrectionFileName
        self.idxDofFileName = idxDofFileName

        self._readSetting()

    def _readSetting(self):
        
        filePath = os.path.join(self.configDir, self.configFileName)
        arrayParamList = ["izn3", "icomp"]

        self.strategy = getSetting(filePath, "estimator_strategy",
                                   arrayParamList)

        # Get the number of z4 - zn
        self.zn3Max = getSetting(filePath, "znmax", arrayParamList)
        self.zn3Max = int(self.zn3Max)-3

        # Get the index groups of z4-zn and DOF
        self.zn3Idx = getSetting(filePath, "izn3", arrayParamList)
        self.zn3Idx = self._getNonZeroIdxFronStrArray(self.zn3Idx)

        self.dofIdx = getSetting(filePath, "icomp", arrayParamList)
        self.dofIdx = self._getNonZeroIdxFronStrArray(self.dofIdx)

        # Read the sensitivity matrix file
        fileName = self._getSenMfileName(reMatchStr="\AsenM\S+")
        shape = self._getSenMshape(fileName)

        print(shape)


    def _getNonZeroIdxFronStrArray(self, strArray):
        """Get the non-zero index array from the string array.

        Parameters
        ----------
        strArray : str
            String array.

        Returns
        -------
        [ndarray]
            Non-zero index array
        """
        
        array = np.array(strArray.split(), dtype=int)
        nonZeroIdxArray = np.where(array!=0)[0]

        return nonZeroIdxArray

    def _getSenMfileName(self, reMatchStr):
        """Get the sensitivity matrix M file name.

        Parameters
        ----------
        reMatchStr : str
            Matching string for the regular expression.

        Returns
        -------
        str
            Sensitivity matrix M file name.
        """

        dirPath = os.path.join(self.configDir, self.instName.name)
        filePaths = getDirFiles(dirPath)
        matchFilePath = getMatchFilePath(reMatchStr, filePaths)
        senMFileName = os.path.basename(matchFilePath)

        return senMFileName

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

    def estiOptState(self):
        pass

    def getDofIdx(self):
        pass

    def getEffWave(self):
        pass

    def getFieldIdx(self):
        pass

    def getGroupIdxAndLeng(self):
        pass
        
    def getPinvA(self):
        pass

    def getSenA(self):
        pass

    def getSenM(self):
        pass

    def getWfFromFile(self):
        pass

    def getWfFromShwfsFile(self):
        pass

    def getY2Corr(self):
        pass

    def getZkAndDofInGroups(self):
        pass

    def getZn3Idx(self):
        pass

    def setAandPinvA(self):
        pass

    def setZkAndDofInGroups(self):
        pass

    def _setSenA(self):
        pass

    def _setPinvA(self):
        pass

    def _getIntrincZk(self):
        pass

    def _setSenM(self):
        pass


if __name__ == "__main__":
    
    optStateEsti = OptStateEsti()

    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"
    optStateEsti.config(configDir, instName=InstName.LSST)