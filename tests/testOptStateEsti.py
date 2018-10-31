import os
import unittest


if __name__ == "__main__":
    
    # Run the unit test
    unittest.main()

    # optStateEsti = OptStateEsti()

    # configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"
    # optStateEsti.config(configDir, instName=InstName.LSST)
    # optStateEsti.setAandPinvA([0, 1, 2])
    # fieldIdx = optStateEsti.getFieldIdx(["R22_S11", "R22_S12"])
    # effWave = optStateEsti.getEffWave(FilterType.REF)
    # y2c = optStateEsti.getY2Corr(fieldIdx, isNby1Array=True)

    # startIdx, groupLeng = optStateEsti.getGroupIdxAndLeng(DofGroup.M2Bend)

    # # zn3Idx = [1, 2, 3]
    # # dofIdx = [3, 4, 5, 6,7]
    # # optStateEsti.setZkAndDofIdxArrays(zn3Idx, dofIdx)

    # # zkToUse = [0,0,1,1,1,1,0,0,0,1,1,1,1,1,0,0,0,0,0]
    # # camHexPos = [0,0,0,0,0]
    # # optStateEsti.setZkAndDofInGroups(zkToUse=zkToUse, camHexPos=camHexPos)

    # testDataDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/tests/testData"
    # testWfsFile = "lsst_wfs_error_iter0.z4c"
    # testWfsFilePath = os.path.join(testDataDir, testWfsFile)

    # sensorNameArray = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]
    # wfErr, fieldIdx = optStateEsti.getWfAndFieldIdFromFile(testWfsFilePath, sensorNameArray)

    # # testShwfsFilePath = os.path.join(testDataDir, "shwfs_wfs_error.txt")
    # # optStateEsti.getWfAndFieldIdFromShwfsFile(testShwfsFilePath)

    # # intrinsicZk = optStateEsti._getIntrinsicZk(FilterType.REF, fieldIdx)
    # optStateEsti.setAandPinvA(fieldIdx)
    # optState = optStateEsti.estiOptState(FilterType.REF, wfErr, fieldIdx)