import os
import numpy as np
import unittest

from lsst.ts.ofc.ParamReader import ParamReader
from lsst.ts.ofc.Utility import getModulePath


class TestParamReader(unittest.TestCase):
    """Test the Utility functions."""

    def setUp(self):

        self.configDir = os.path.join(getModulePath(), "tests", "testData")
        self.fileName = "zkAndDofIdxArraySet.txt"

        filePath = os.path.join(self.configDir, self.fileName)
        self.paramReader = ParamReader(filePath)

    def testGetSetting(self):

        arrayParamList = ["icomp", "izn3"]
        znmax = self.paramReader.getSetting("znmax",
                                            arrayParamList=arrayParamList)
        self.assertEqual(znmax, "22")

        icomp = self.paramReader.getSetting("icomp",
                                            arrayParamList=arrayParamList)
        icomp = np.array(icomp.split(), dtype=int)
        self.assertEqual(np.sum(icomp), 10)

        izn3 = self.paramReader.getSetting("izn3",
                                           arrayParamList=arrayParamList)
        izn3 = np.array(izn3.split(), dtype=int)
        self.assertEqual(np.sum(izn3), 12)

        self.assertRaises(ValueError, self.paramReader.getSetting,
                          "notThisSetting")

    def testGetContent(self):

        content = self.paramReader.getTxtContent()
        contentList = content.splitlines()
        self.assertEqual(len(contentList), 24)

    def testFilePath(self):

        ansFilePath = os.path.join(self.configDir, self.fileName)
        self.assertEqual(self.paramReader.getFilePath(), ansFilePath)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
