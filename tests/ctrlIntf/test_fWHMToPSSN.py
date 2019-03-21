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

        testDataFilePath = os.path.join(self.testDataDir,
                                        "lsst_iter0_PSSN.txt")
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
