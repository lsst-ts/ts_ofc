import os
import unittest
import numpy as np

from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.Utility import InstName, DofGroup


class TestDataShare(unittest.TestCase):
    """Test the DataShare class."""

    def setUp(self):

        self.dataShare = DataShare()
        self.configDir = os.path.join("..", "configData")
        self.dataShare.config(self.configDir, instName=InstName.LSST)

    def testLsstSetting(self):

        self.assertEqual(self.dataShare.getConfigDir(), self.configDir)

        instDirPath = os.path.join(self.configDir, "lsst")
        self.assertEqual(self.dataShare.getInstDir(), instDirPath)

        dofIdx = self.dataShare.getDofIdx()
        self.assertEqual(len(dofIdx), 50)
        self.assertEqual(dofIdx[0], 0)
        self.assertEqual(dofIdx[-1], 49)

        zn3Idx = self.dataShare.getZn3Idx()
        self.assertEqual(len(zn3Idx), 19)
        self.assertEqual(zn3Idx[0], 0)
        self.assertEqual(zn3Idx[-1], 18)

        senM = self.dataShare.getSenM()
        self.assertEqual(senM.shape, (35, 19, 50))
        self.assertEqual(senM[4, 3, 5], -1.1726e-11)

        self.assertEqual(self.dataShare.zn3Max, 19)

    def testComCamSetting(self):

        dataShare = DataShare()
        dataShare.config(self.configDir, instName=InstName.COMCAM)

        instDirPath = os.path.join(self.configDir, "comcam")
        self.assertEqual(dataShare.getInstDir(), instDirPath)
        self.assertEqual(dataShare.getSenM().shape, (9, 19, 50))

    def testSenMShape(self):

        dataShare = DataShare()
        configDir = os.path.join(".", "testData")

        self.assertRaises(ValueError, dataShare.config, configDir,
                          InstName.LSST)
        self.assertRaises(ValueError, dataShare.config, configDir,
                          InstName.COMCAM)

    def testGetFieldIdx(self):

        sensorNameList = ["R04_S20", "R10_S02"]
        fieldIdx = self.dataShare.getFieldIdx(sensorNameList)
        self.assertEqual(fieldIdx, [32, 23])

        sensorNameList = []
        fieldIdx = self.dataShare.getFieldIdx(sensorNameList)
        self.assertEqual(fieldIdx, [])

        sensorNameList = ["R04_S20", "R04_S20"]
        fieldIdx = self.dataShare.getFieldIdx(sensorNameList)
        self.assertEqual(fieldIdx, [32, 32])

        sensorNameList = "R04_S20"
        self.assertRaises(TypeError, self.dataShare.getFieldIdx,
                          sensorNameList)

    def testGetGroupIdxAndLeng(self):

        dofGroupList = [DofGroup.M2HexPos, DofGroup.CamHexPos,
                        DofGroup.M1M3Bend, DofGroup.M2Bend]
        startIdxList = [0, 5, 10, 30]
        groupLengList = [5, 5, 20, 20]
        for startIdx, groupLeng, dofGroup in zip(startIdxList,
                                                 groupLengList, dofGroupList):
            dofStartIdx, dofGroupLeng = self.dataShare.getGroupIdxAndLeng(
                                                                    dofGroup)
            self.assertEqual((dofStartIdx, dofGroupLeng),
                             (startIdx, groupLeng))

        self.assertRaises(ValueError, self.dataShare.getGroupIdxAndLeng,
                          "NoThisGroup")
        self.assertRaises(ValueError, self.dataShare.getGroupIdxAndLeng,
                          InstName.LSST)
        self.assertRaises(ValueError, self.dataShare.getGroupIdxAndLeng, "")

    def testSetZkAndDofIdxArrays(self):

        zn3Idx = np.arange(3, 9)
        dofIdx = np.arange(1, 40, 3)
        self.dataShare.setZkAndDofIdxArrays(zn3Idx, dofIdx)

        self.assertEqual(np.sum(self.dataShare.getZn3Idx()-zn3Idx), 0)
        self.assertEqual(np.sum(self.dataShare.getDofIdx()-dofIdx), 0)

        senM = self.dataShare.getSenM()
        self.assertEqual(senM.shape, (35, 6, 13))
        self.assertEqual(senM[4, 3, 5], -6.8834e-03)

    def testSetZkAndDofInGroups(self):

        idxToBeZero = np.array([1, 3, 4, 5, 7])
        zkToUse = np.ones(19, dtype=int)
        zkToUse[idxToBeZero] = 0

        camHexPos = np.zeros(5, dtype=int)

        self.dataShare.setZkAndDofInGroups(zkToUse=zkToUse,
                                           camHexPos=camHexPos)

        zkToUseInDataShare = self.dataShare.getZn3Idx()
        for idx in idxToBeZero:
            self.assertNotIn(idx, zkToUseInDataShare)

        dofIdxInDataShate = self.dataShare.getDofIdx()
        camHexPosIdx = np.arange(5, 10)
        for idx in camHexPosIdx:
            self.assertNotIn(idx, dofIdxInDataShate)

        self.assertEqual(self.dataShare.getSenM().shape, (35, 14, 45))

        incorrectZkToUse = np.ones(20, dtype=int)
        self.assertRaises(ValueError, self.dataShare.setZkAndDofInGroups,
                          incorrectZkToUse)

        incorrectCamHexPos = np.zeros(4, dtype=int)
        self.assertRaises(ValueError, self.dataShare.setZkAndDofInGroups,
                          zkToUse, incorrectCamHexPos)

    def testGetWfAndFieldIdFromFile(self):

        wfFilePath = os.path.join(".", "testData", "lsst_wfs_error_iter0.z4c")
        sensorNameList = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]
        wfErr, fieldIdx = self.dataShare.getWfAndFieldIdFromFile(
                                        wfFilePath, sensorNameList)
        self.assertEqual(wfErr.shape, (4, 19))
        self.assertEqual(fieldIdx, [31, 32, 33, 34])

        incorrectSensorNameList = ["R44_S00", "R04_S20", "R00_S22"]
        self.assertRaises(ValueError, self.dataShare.getWfAndFieldIdFromFile,
                          wfFilePath, incorrectSensorNameList)

    def testGetWfAndFieldIdFromShwfsFile(self):

        wfFilePath = os.path.join(".", "testData", "shwfs_wfs_error.txt")
        sensorName = "R22_S11"
        wfErr, fieldIdx = self.dataShare.getWfAndFieldIdFromShwfsFile(
                                        wfFilePath, sensorName=sensorName)

        self.assertEqual(len(wfErr), 19)
        self.assertEqual(fieldIdx, [0])
        self.assertEqual(wfErr[0], 1000)

    def testMapSensorIdToName(self):

        sensorIdList = [1, 2, 3, 4]
        sensorNameList, numOfsensor = self.dataShare.mapSensorIdToName(
                                                            sensorIdList)
        self.assertEqual(sensorNameList,
                         ["R00_S21", "R00_S22", "R01_S00", "R01_S01"])
        self.assertEqual(numOfsensor, 4)

        sensorIdList = [1, -1]
        sensorNameList, numOfsensor = self.dataShare.mapSensorIdToName(
                                                            sensorIdList)
        self.assertEqual(sensorNameList, ["R00_S21"])
        self.assertEqual(numOfsensor, 1)

        sensorIdList = []
        sensorNameList, numOfsensor = self.dataShare.mapSensorIdToName(
                                                            sensorIdList)
        self.assertEqual(sensorNameList, [])
        self.assertEqual(numOfsensor, 0)

    def testMapSensorNameToId(self):

        sensorNameList = ["R00_S21", "R00_S22", "R01_S00", "R01_S01"]
        sensorIdList = self.dataShare.mapSensorNameToId(sensorNameList)
        self.assertEqual(sensorIdList, [1, 2, 3, 4])

        sensorNameList = []
        sensorIdList = self.dataShare.mapSensorNameToId(sensorNameList)
        self.assertEqual(sensorIdList, [])

        incorrectSensorNameList = ["R00_S21", "R000_S1111"]
        self.assertRaises(ValueError, self.dataShare.mapSensorNameToId,
                          incorrectSensorNameList)

        incorrectSensorNameList = "R00_S21"
        self.assertRaises(TypeError, self.dataShare.mapSensorNameToId,
                          incorrectSensorNameList)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
