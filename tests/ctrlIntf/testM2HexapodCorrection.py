import unittest

from lsst.ts.ofc.ctrlIntf.M2HexapodCorrection import M2HexapodCorrection


class TestM2HexapodCorrection(unittest.TestCase):
    """Test the M2HexapodCorrection class."""

    def setUp(self):

        self.xTilt = 0.1
        self.yTilt = 0.2
        self.piston = 0.3
        self.m2HexapodCorrection = M2HexapodCorrection(self.xTilt, self.yTilt,
                                                       self.piston)

    def testGetCorrection(self):

        xTilt, yTilt, piston = self.m2HexapodCorrection.getCorrection()
        self.assertEqual(xTilt, self.xTilt)
        self.assertEqual(yTilt, self.yTilt)
        self.assertEqual(piston, self.piston)

    def testSetCorrection(self):

        xTilt = 0.2
        yTilt = 0.3
        piston = 0.4
        self.m2HexapodCorrection.setCorrection(xTilt, yTilt, piston)

        xTiltInM2, yTiltInM2, pistonInM2 = \
            self.m2HexapodCorrection.getCorrection()
        self.assertEqual(xTiltInM2, xTilt)
        self.assertEqual(yTiltInM2, yTilt)
        self.assertEqual(pistonInM2, piston)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
