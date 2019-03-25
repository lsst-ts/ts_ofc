import numpy as np
import unittest

from lsst.ts.ofc.BendModeToForce import BendModeToForce
from lsst.ts.ofc.Utility import DofGroup, getConfigDir


class TestBendModeToForce(unittest.TestCase):
    """Test the BendModeToForce class."""

    def setUp(self):

        self.configDir = getConfigDir()
        self.bendModeToForce = BendModeToForce()

    def testGetRotMat(self):

        self.assertEqual(len(self.bendModeToForce.getRotMat()), 0)

    def _configM1M3(self):

        self.bendModeToForce.config(self.configDir, DofGroup.M1M3Bend,
                                    "M1M3_1um_156_force.yaml")

    def testConfig(self):

        self._configM1M3()

        rotMat = self.bendModeToForce.getRotMat()
        self.assertEqual(rotMat.shape, (156, 20))
        self.assertEqual(rotMat[0, 0], 0.26501543)
        self.assertEqual(rotMat[0, 1], -0.96061351)
        self.assertEqual(rotMat[1, 0], 0.65245336)
        self.assertEqual(rotMat[1, 1], -2.8548595)

    def testCalcActForceOfM1M3(self):

        self._configM1M3()
        actForce = self._calcActForce()[0]

        self.assertEqual(len(actForce), 156)
        self.assertEqual(actForce[0], 121.44954441)

    def _calcActForce(self):

        mirrorDof = np.zeros(20)
        mirrorDof[0:3] = np.array([1, 2, 3])
        actForce = self.bendModeToForce.calcActForce(mirrorDof)

        return actForce, mirrorDof

    def testCalcActForceOfM2(self):

        self._configM2()
        actForce = self._calcActForce()[0]

        self.assertEqual(len(actForce), 156)
        self.assertEqual(actForce[0], 121.44954441)

    def _configM2(self):

        self.bendModeToForce.config(self.configDir, DofGroup.M2Bend,
                                    "M2_1um_force.yaml")

    def testEstiBendingMode(self):

        self._configM1M3()
        actForce, mirrorDof = self._calcActForce()

        bendingMode = self.bendModeToForce.estiBendingMode(actForce)

        delta = np.sum(np.abs(bendingMode - mirrorDof))
        self.assertLess(delta, 1e-10)

    def testGetMirrorDirName(self):

        self.assertEqual(BendModeToForce.getMirrorDirName(DofGroup.M1M3Bend),
                         "M1M3")
        self.assertEqual(BendModeToForce.getMirrorDirName(DofGroup.M2Bend),
                         "M2")
        self.assertRaises(ValueError, BendModeToForce.getMirrorDirName,
                          DofGroup.M2HexPos)

    def testCheckDofGroupIsMirrorWithError(self):

        self.assertRaises(ValueError, BendModeToForce.checkDofGroupIsMirror,
                          DofGroup.CamHexPos)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
