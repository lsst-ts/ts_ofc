import unittest
import numpy as np

from lsst.ts.ofc.ctrlIntf.M1M3Correction import M1M3Correction


class TestM1M3Correction(unittest.TestCase):
    """Test the M1M3Correction class."""

    def setUp(self):

        self.zForces = np.arange(M1M3Correction.NUM_OF_ACT)
        self.m1m3Correction = M1M3Correction(self.zForces)

    def testGetZForces(self):

        zForces = self.m1m3Correction.getZForces()
        self.assertTrue(isinstance(zForces, np.ndarray))

        delta = np.sum(np.abs(zForces - self.zForces))
        self.assertEqual(delta, 0)

    def testSetZForces(self):

        zForces = np.arange(M1M3Correction.NUM_OF_ACT) * 10
        self.m1m3Correction.setZForces(zForces)

        zForcesInM1M3 = self.m1m3Correction.getZForces()
        delta = np.sum(np.abs(zForcesInM1M3 - zForces))
        self.assertEqual(delta, 0)

    def testSetZForcesWithWrongLength(self):

        zForces = np.arange(M1M3Correction.NUM_OF_ACT + 1)
        self.assertRaises(ValueError, self.m1m3Correction.setZForces, zForces)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
