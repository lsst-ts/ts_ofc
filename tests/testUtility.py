import os
import unittest

from lsst.ts.ofc.Utility import getDirFiles, getMatchFilePath, getModulePath


class TestUtility(unittest.TestCase):
    """Test the Utility functions."""

    def setUp(self):

        self.configDir = os.path.join(getModulePath(), "tests", "testData")

    def testGetDirFiles(self):

        filePaths = getDirFiles(self.configDir)
        self.assertEqual(len(filePaths), 7)

    def testGetMatchFilePath(self):

        reMatchStr = r"\Alsst\S+iter1\S+"
        filePaths = getDirFiles(self.configDir)
        matchFilePath = getMatchFilePath(reMatchStr, filePaths)
        self.assertEqual(os.path.basename(matchFilePath),
                         "lsst_pert_iter1.txt")

        reMatchStr = r"\Alsst\S+iter2\S+"
        self.assertRaises(FileNotFoundError, getMatchFilePath, reMatchStr,
                          filePaths)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
