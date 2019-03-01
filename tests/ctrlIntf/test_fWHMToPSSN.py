import unittest
import numpy as np

from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN


class TestFWHMToPSSN(unittest.TestCase):

    def setUp(self):

        self.fwhmToPssn = FWHMToPSSN()

    def testConvertToPssn(self):

        numOfData = 3
        fwhm = np.ones(numOfData)

        pssn = self.fwhmToPssn.convertToPssn(fwhm)
        self.assertEqual(len(pssn), numOfData)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
