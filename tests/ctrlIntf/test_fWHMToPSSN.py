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
import unittest

from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN
from lsst.ts.ofc.Utility import getModulePath


class TestFWHMToPSSN(unittest.TestCase):
    def setUp(self):

        self.fwhmToPssn = FWHMToPSSN()
        self.testDataDir = os.path.join(getModulePath(), "tests", "testData")

    def testConvertToPssn(self):

        testDataFilePath = os.path.join(self.testDataDir, "lsst_iter0_PSSN.txt")
        testData = np.loadtxt(testDataFilePath)
        pssnAns = testData[0, :-1]
        fwhm = testData[1, :-1]

        pssn = self.fwhmToPssn.convertToPssn(fwhm)

        self.assertEqual(len(pssn), len(fwhm))

        delta = np.sum(np.abs(pssn - pssnAns))
        self.assertLess(delta, 1e-10)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
