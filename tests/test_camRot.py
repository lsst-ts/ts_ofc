import numpy as np
import unittest

from lsst.ts.ofc.CamRot import CamRot
from lsst.ts.ofc.Utility import DofGroup


class TestCamRot(unittest.TestCase):
    """Test the CamRot class."""

    def setUp(self):

        self.camRot = CamRot()

    def testSetAndGetRotAng(self):

        rotAngInDeg = 45
        self.camRot.setRotAng(rotAngInDeg)
        self.assertEqual(self.camRot.getRotAng(), rotAngInDeg)

    def testSetRotAngWithWrongValue(self):

        self.assertRaises(ValueError, self.camRot.setRotAng, -91)
        self.assertRaises(ValueError, self.camRot.setRotAng, 91)

    def testRotGroupDofOfM2Hex(self):

        self.camRot.setRotAng(45)
        dofGroup = DofGroup.M2HexPos
        stateInDof = [1, 2, 2, 4, 4]
        tiltXYinArcsec = (1224, 0)
        rotatedStateInDof = self.camRot.rotGroupDof(dofGroup, stateInDof,
                                                    tiltXYinArcsec)

        self.assertAlmostEqual(rotatedStateInDof[1], 0.00841705, places=7)

    def testRotGroupDofOfCamHex(self):

        self.camRot.setRotAng(90)
        dofGroup = DofGroup.CamHexPos
        stateInDof = [1, 2, 3, 4, 5]
        tiltXYinArcsec = (0, 0)
        rotatedStateInDof = self.camRot.rotGroupDof(dofGroup, stateInDof,
                                                    tiltXYinArcsec)

        ans = [1, -3, 2, -5, 4]
        delta = np.sum(np.abs(rotatedStateInDof - ans))
        self.assertEqual(delta, 0)

    def testRotGroupDofOfM1M3Bend(self):

        self.camRot.setRotAng(45)
        dofGroup = DofGroup.M1M3Bend

        numOfBendMode = 20
        stateInDof = np.zeros(numOfBendMode)
        stateInDof[0] = 1
        stateInDof[2] = 2
        tiltXYinArcsec = (0, 0)

        rotatedStateInDof = self.camRot.rotGroupDof(dofGroup, stateInDof,
                                                    tiltXYinArcsec)

        self.assertAlmostEqual(rotatedStateInDof[0], 0.70710678, places=7)
        self.assertEqual(rotatedStateInDof[2], 2)
        self.assertEqual(len(rotatedStateInDof), numOfBendMode)

    def testRotGroupDofOfM2Bend(self):

        self.camRot.setRotAng(45)
        dofGroup = DofGroup.M2Bend

        numOfBendMode = 20
        stateInDof = np.zeros(numOfBendMode)
        stateInDof[0] = 1
        stateInDof[4] = 2
        tiltXYinArcsec = (0, 0)

        rotatedStateInDof = self.camRot.rotGroupDof(dofGroup, stateInDof,
                                                    tiltXYinArcsec)

        self.assertAlmostEqual(rotatedStateInDof[0], 0.70710678, places=7)
        self.assertEqual(rotatedStateInDof[4], 2)
        self.assertEqual(len(rotatedStateInDof), numOfBendMode)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
