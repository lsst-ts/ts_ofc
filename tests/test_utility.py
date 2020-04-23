import os
import numpy as np
import tempfile
import unittest

from lsst.ts.ofc.Utility import getDirFiles, getMatchFilePath, getModulePath, \
    rot1dArray


class TestUtility(unittest.TestCase):
    """Test the Utility functions."""

    def setUp(self):

        self.configDir = os.path.join(getModulePath(), "tests", "testData")

    def testGetDirFiles(self):

        dataDirPath = os.path.join(getModulePath(), "tests")
        dataDir = tempfile.TemporaryDirectory(dir=dataDirPath)

        filePaths = getDirFiles(dataDir.name)
        self.assertEqual(len(filePaths), 0)

        with tempfile.NamedTemporaryFile(dir=dataDir.name):
            filePathsUpdate = getDirFiles(dataDir.name)
            self.assertEqual(len(filePathsUpdate), 1)

        dataDir.cleanup()

    def testGetMatchFilePath(self):

        reMatchStr = r"\Alsst\S+iter1\S+"
        filePaths = getDirFiles(self.configDir)
        matchFilePath = getMatchFilePath(reMatchStr, filePaths)
        self.assertEqual(os.path.basename(matchFilePath),
                         "lsst_pert_iter1.txt")

        reMatchStr = r"\Alsst\S+iter2\S+"
        self.assertRaises(FileNotFoundError, getMatchFilePath, reMatchStr,
                          filePaths)

    def testRot1dArray(self):

        rotMat = np.array([[1, 2], [3, 4]])
        array = np.array([5, 6])
        rotArray = rot1dArray(array, rotMat)

        self.assertEqual(rotArray.tolist(), [17, 39])


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
