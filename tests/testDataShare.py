import os
import unittest
import numpy as np

from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.Utility import InstName, FilterType, DofGroup


if __name__ == "__main__":
    
    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"

    dataShare = DataShare()
    dataShare.config(configDir, instName=InstName.LSST)

    fieldIdx = dataShare.getFieldIdx(["R22_S11", "R22_S12"])

    startIdx, groupLeng = dataShare.getGroupIdxAndLeng(DofGroup.M2Bend)

    # zn3Idx = [1, 2, 3]
    # dofIdx = [3, 4, 5, 6,7]
    # dataShare.setZkAndDofIdxArrays(zn3Idx, dofIdx)

    # zkToUse = [0,0,1,1,1,1,0,0,0,1,1,1,1,1,0,0,0,0,0]
    # camHexPos = [0,0,0,0,0]
    # dataShare.setZkAndDofInGroups(zkToUse=zkToUse, camHexPos=camHexPos)

    testDataDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/tests/testData"
    testWfsFile = "lsst_wfs_error_iter0.z4c"
    testWfsFilePath = os.path.join(testDataDir, testWfsFile)

    sensorNameArray = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]
    wfErr, fieldIdx = dataShare.getWfAndFieldIdFromFile(testWfsFilePath, sensorNameArray)

    testShwfsFilePath = os.path.join(testDataDir, "shwfs_wfs_error.txt")
    wfErr, fieldIdx = dataShare.getWfAndFieldIdFromShwfsFile(testShwfsFilePath)
