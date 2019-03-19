import numpy as np
import unittest

from lsst.ts.ofc.SubSysAdap import SubSysAdap
from lsst.ts.ofc.Utility import DofGroup, getConfigDir


class TestSubSysAdap(unittest.TestCase):
    """Test the SubSysAdap class."""

    def setUp(self):

        self.configDir = getConfigDir()

        self.subSysAdap = SubSysAdap()
        self.subSysAdap.config(self.configDir)

    def testConfig(self):

        self._testRotMatShape(self.subSysAdap, DofGroup.M2HexPos, (5, 6))
        self._testRotMatShape(self.subSysAdap, DofGroup.CamHexPos, (5, 6))
        self._testRotMatShape(self.subSysAdap, DofGroup.M1M3Bend, (20, 20))
        self._testRotMatShape(self.subSysAdap, DofGroup.M2Bend, (20, 20))

    def _testRotMatShape(self, subSysAdap, dofGroup, ansShape):

        rotMat = subSysAdap.getRotMatInDof(dofGroup)
        self.assertEqual(rotMat.shape, ansShape)

    def testGetRotMatInDof(self):

        subSysAdap = SubSysAdap()

        self._testRotMatShape(subSysAdap, DofGroup.M2HexPos, (0, ))
        self._testRotMatShape(subSysAdap, DofGroup.CamHexPos, (0, ))
        self._testRotMatShape(subSysAdap, DofGroup.M1M3Bend, (0, ))
        self._testRotMatShape(subSysAdap, DofGroup.M2Bend, (0, ))

    def testTransActForceToZemaxWithWrongInputDofGroup(self):

        self.assertRaises(ValueError, self.subSysAdap.transActForceToSubSys,
                          DofGroup.M2HexPos, np.array([0]))

    def testTransActForceToZemax(self):

        actForce = np.ones(156)
        transActForce = self.subSysAdap.transActForceToZemax(
            DofGroup.M1M3Bend, actForce)

        ansActForce = -actForce
        delta = np.sum(np.abs(transActForce - ansActForce))
        self.assertEqual(delta, 0)

    def testTransActForceToSubSys(self):

        actForce = np.ones(156)
        transActForce = self.subSysAdap.transActForceToSubSys(
            DofGroup.M1M3Bend, actForce)

        ansActForce = -actForce
        delta = np.sum(np.abs(transActForce - ansActForce))
        self.assertEqual(delta, 0)

    def testTransBendingModeToZemax(self):

        mirrorBend = np.ones(20)
        transMirrorBend = self.subSysAdap.transBendingModeToZemax(
            DofGroup.M1M3Bend, mirrorBend)

        self.assertEqual(len(transMirrorBend), 20)
        self.assertEqual(transMirrorBend[1], -1)

    def testTransBendingModeToSubSys(self):

        mirrorBend = np.ones(20)
        transMirrorBend = self.subSysAdap.transBendingModeToSubSys(
            DofGroup.M1M3Bend, mirrorBend)

        self.assertEqual(len(transMirrorBend), 20)
        self.assertEqual(transMirrorBend[1], -1)

    def testTransHexaPosToZemax(self):

        hexaPos = np.array([1, 2, 3, 1, 1, 1])
        transHexPos = self.subSysAdap.transHexaPosToZemax(hexaPos)

        ansHexPos = [-3, -1, 2, -3600, 3600]
        self.assertEqual(transHexPos.tolist(), ansHexPos)

    def testTransHexaPosToSubSys(self):

        hexaPos = np.array([1, 2, 3, 3600, 3600])
        transHexPos = self.subSysAdap.transHexaPosToSubSys(hexaPos)

        ansHexPos = [-2, 3, -1, -1, 1, 0]
        self.assertEqual(transHexPos.tolist(), ansHexPos)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
