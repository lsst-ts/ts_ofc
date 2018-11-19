import os
import numpy as np
import unittest

from lsst.ts.ofc.Utility import getSetting, getDirFiles, getMatchFilePath, \
                                getModulePath


class TestUtility(unittest.TestCase):
    """Test the Utility functions."""

    def setUp(self):

        self.configDir = os.path.join(getModulePath(), "tests", "testData")

    def testGetSetting(self):

        configFileName = "dataShare.txt"
        filePath = os.path.join(self.configDir, configFileName)

        arrayParamList = ["icomp", "izn3"]
        znmax = getSetting(filePath, "znmax", arrayParamList=arrayParamList)
        self.assertEqual(znmax, "22")

        icomp = getSetting(filePath, "icomp", arrayParamList=arrayParamList)
        icomp = np.array(icomp.split(), dtype=int)
        self.assertEqual(np.sum(icomp), 10)

        izn3 = getSetting(filePath, "izn3", arrayParamList=arrayParamList)
        izn3 = np.array(izn3.split(), dtype=int)
        self.assertEqual(np.sum(izn3), 12)

        self.assertRaises(ValueError, getSetting, filePath,
                          "notThisSetting")

    def testGetDirFiles(self):

        filePaths = getDirFiles(self.configDir)
        self.assertEqual(len(filePaths), 7)

    def testGetMatchFilePath(self):

        reMatchStr = "\Alsst\S+iter1\S+"
        filePaths = getDirFiles(self.configDir)
        matchFilePath = getMatchFilePath(reMatchStr, filePaths)
        self.assertEqual(os.path.basename(matchFilePath),
                         "lsst_pert_iter1.txt")

        reMatchStr = "\Alsst\S+iter2\S+"
        self.assertRaises(FileNotFoundError, getMatchFilePath, reMatchStr,
                          filePaths)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
