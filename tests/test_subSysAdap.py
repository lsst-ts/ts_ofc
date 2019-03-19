import unittest

from lsst.ts.ofc.SubSysAdap import SubSysAdap
from lsst.ts.ofc.Utility import DofGroup, getConfigDir


class TestSubSysAdap(unittest.TestCase):
    """Test the SubSysAdap class."""

    def setUp(self):

        self.configDir = getConfigDir()
        self.subSysAdap = SubSysAdap()

    def testConfig(self):

        self._config()

        self._testRotMatShape(DofGroup.M2HexPos, (5, 6))
        self._testRotMatShape(DofGroup.CamHexPos, (5, 6))
        self._testRotMatShape(DofGroup.M1M3Bend, (20, 20))
        self._testRotMatShape(DofGroup.M2Bend, (20, 20))

    def _config(self):

        self.subSysAdap.config(self.configDir)

    def _testRotMatShape(self, dofGroup, ansShape):

        rotMat = self.subSysAdap.getRotMatInDof(dofGroup)
        self.assertEqual(rotMat.shape, ansShape)

    def testGetRotMatInDof(self):

        self._testRotMatShape(DofGroup.M2HexPos, (0, ))
        self._testRotMatShape(DofGroup.CamHexPos, (0, ))
        self._testRotMatShape(DofGroup.M1M3Bend, (0, ))
        self._testRotMatShape(DofGroup.M2Bend, (0, ))


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
