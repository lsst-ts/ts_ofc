import numpy as np
import unittest

from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfIota import OFCCalculationOfIota


class TestOFCCalculationOfIota(unittest.TestCase):
    """Test the OFCCalculationOfIota class."""

    def setUp(self):

        self.ofcCalculation = OFCCalculationOfIota(InstName.COMCAM, "sh")

    def testZkAndDofIdxFromConfigFile(self):

        dataShare = self.ofcCalculation.ztaac.dataShare
        zn3Idx = dataShare.getZn3Idx()
        dofIdx = dataShare.getDofIdx()

        ansZn3Idx = np.arange(19)
        ansDofIdx = np.arange(10)

        deltaZn3 = np.sum(np.abs(zn3Idx - ansZn3Idx))
        deltaDof = np.sum(np.abs(dofIdx - ansDofIdx))

        self.assertEqual(deltaZn3, 0)
        self.assertEqual(deltaDof, 0)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
