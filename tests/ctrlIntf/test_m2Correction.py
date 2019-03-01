import unittest
import numpy as np

from lsst.ts.ofc.ctrlIntf.M2Correction import M2Correction


class TestM2Correction(unittest.TestCase):
    """Test the M2Correction class."""

    def setUp(self):

        self.zForces = np.arange(M2Correction.NUM_OF_ACT)
        self.m2Correction = M2Correction(self.zForces)

    def testGetZForces(self):

        zForces = self.m2Correction.getZForces()
        self.assertTrue(isinstance(zForces, np.ndarray))

        delta = np.sum(np.abs(zForces - self.zForces))
        self.assertEqual(delta, 0)

    def testSetZForces(self):

        zForces = np.arange(M2Correction.NUM_OF_ACT) * 10
        self.m2Correction.setZForces(zForces)

        zForcesInM1M3 = self.m2Correction.getZForces()
        delta = np.sum(np.abs(zForcesInM1M3 - zForces))
        self.assertEqual(delta, 0)

    def testSetZForcesWithWrongLength(self):

        zForces = np.arange(M2Correction.NUM_OF_ACT + 1)
        self.assertRaises(ValueError, self.m2Correction.setZForces, zForces)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
