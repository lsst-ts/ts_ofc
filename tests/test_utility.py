# This file is part of ts_ofc.
#
# Developed for the LSST Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import numpy as np
import tempfile
import unittest

from lsst.ts.ofc.Utility import getDirFiles, getMatchFilePath, getModulePath, rot1dArray


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
        self.assertEqual(os.path.basename(matchFilePath), "lsst_pert_iter1.txt")

        reMatchStr = r"\Alsst\S+iter2\S+"
        self.assertRaises(FileNotFoundError, getMatchFilePath, reMatchStr, filePaths)

    def testRot1dArray(self):

        rotMat = np.array([[1, 2], [3, 4]])
        array = np.array([5, 6])
        rotArray = rot1dArray(array, rotMat)

        self.assertEqual(rotArray.tolist(), [17, 39])


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
