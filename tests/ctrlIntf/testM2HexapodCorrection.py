import unittest

from lsst.ts.ofc.ctrlIntf.M2HexapodCorrection import M2HexapodCorrection


class TestM2HexapodCorrection(unittest.TestCase):
    """Test the M2HexapodCorrection class."""

    def setUp(self):

        self.x = 0.1
        self.y = 0.2
        self.z = 0.3
        self.u = 0.4
        self.v = 0.5
        self.w = 0.6
        self.hexapodCorrection = M2HexapodCorrection(
                            self.x, self.y, self.z, self.u, self.v, w=self.w)

    def testGetCorrection(self):

        x, y, z, u, v, w = self.hexapodCorrection.getCorrection()
        self.assertEqual(self.x, x)
        self.assertEqual(self.y, y)
        self.assertEqual(self.z, z)
        self.assertEqual(self.u, u)
        self.assertEqual(self.v, v)
        self.assertEqual(self.w, w)

    def testSetCorrection(self):

        x = 0.2
        y = 0.3
        z = 0.4
        u = 0.5
        v = 0.6
        w = 0.7
        self.hexapodCorrection.setCorrection(x, y, z, u, v, w=w)

        xInHex, yInHex, zInHex, uInHex, vInHex, wInHex = \
            self.hexapodCorrection.getCorrection()
        self.assertEqual(xInHex, x)
        self.assertEqual(yInHex, y)
        self.assertEqual(zInHex, z)
        self.assertEqual(uInHex, u)
        self.assertEqual(vInHex, v)
        self.assertEqual(wInHex, w)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
