import os
import shutil
import numpy as np
import unittest

from lsst.ts.ofc.ParamReaderYaml import ParamReaderYaml
from lsst.ts.ofc.Utility import getConfigDir, getModulePath


class TestParamReaderYaml(unittest.TestCase):
    """Test the ParamReaderYaml class."""

    def setUp(self):

        self.configDir = getConfigDir()
        self.fileName = "zkAndDofIdxArraySet.yaml"

        filePath = os.path.join(self.configDir, self.fileName)
        self.paramReader = ParamReaderYaml(filePath=filePath)

        self.testDir = os.path.join(getModulePath(), "tests", "tmp")
        self._makeDir(self.testDir)

    def _makeDir(self, directory):

        if (not os.path.exists(directory)):
            os.makedirs(directory)

    def tearDown(self):

        shutil.rmtree(self.testDir)

    def testGetSetting(self):

        znmax = self.paramReader.getSetting("znmax")
        self.assertEqual(znmax, 22)

    def testGetFilePath(self):

        ansFilePath = os.path.join(self.configDir, self.fileName)
        self.assertEqual(self.paramReader.getFilePath(), ansFilePath)

    def testSetFilePath(self):

        fileName = "test.yaml"
        filePath = os.path.join(self.configDir, fileName)
        self.paramReader.setFilePath(filePath)

        self.assertEqual(self.paramReader.getFilePath(), filePath)

    def testGetContent(self):

        content = self.paramReader.getContent()
        self.assertTrue(isinstance(content, dict))

    def testWriteMatToFile(self):

        self._writeMatToFile()

        numOfFile = self._getNumOfFileInFolder(self.testDir)
        self.assertEqual(numOfFile, 1)

    def _writeMatToFile(self):

        mat = np.random.rand(3, 4, 5)
        filePath = os.path.join(self.testDir, "temp.yaml")
        ParamReaderYaml.writeMatToFile(mat, filePath)

        return mat, filePath

    def _getNumOfFileInFolder(self, folder):

        return len([name for name in os.listdir(folder)
                   if os.path.isfile(os.path.join(folder, name))])

    def testWriteMatToFileWithWrongFileFormat(self):

        wrongFilePath = os.path.join(self.testDir, "temp.txt")
        self.assertRaises(ValueError, ParamReaderYaml.writeMatToFile,
                          np.ones(4), wrongFilePath)

    def testGetMatContent(self):

        mat, filePath = self._writeMatToFile()

        self.paramReader.setFilePath(filePath)
        matInYamlFile = self.paramReader.getMatContent()

        delta = np.sum(np.abs(matInYamlFile - mat))
        self.assertLess(delta, 1e-10)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
