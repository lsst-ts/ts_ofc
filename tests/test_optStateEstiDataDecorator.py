import unittest
import numpy as np

from lsst.ts.wep.Utility import FilterType

from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator
from lsst.ts.ofc.Utility import InstName, getConfigDir


class TestOptStateEstiDataDecorator(unittest.TestCase):
    """Test the OptStateEstiDataDecorator class."""

    def setUp(self):

        dataShare = DataShare()
        configDir = getConfigDir()
        dataShare.config(configDir, instName=InstName.LSST)

        self.optStateEstiData = OptStateEstiDataDecorator(dataShare)
        self.optStateEstiData.configOptStateEstiData()

    def testGetEffWave(self):

        effWave = self.optStateEstiData.getEffWave(FilterType.REF)
        self.assertEqual(effWave, 0.5)

        effWave = self.optStateEstiData.getEffWave(FilterType.U)
        self.assertEqual(effWave, 0.365)

        effWave = self.optStateEstiData.getEffWave(FilterType.G)
        self.assertEqual(effWave, 0.480)

        effWave = self.optStateEstiData.getEffWave(FilterType.R)
        self.assertEqual(effWave, 0.622)

        effWave = self.optStateEstiData.getEffWave(FilterType.I)
        self.assertEqual(effWave, 0.754)

        effWave = self.optStateEstiData.getEffWave(FilterType.Z)
        self.assertEqual(effWave, 0.868)

        effWave = self.optStateEstiData.getEffWave(FilterType.Y)
        self.assertEqual(effWave, 0.973)

    def testGetY2Corr(self):

        fieldIdx = [1, 2, 3]
        y2c = self.optStateEstiData.getY2Corr(fieldIdx)
        getZn3Idx = self.optStateEstiData.getZn3Idx()
        self.assertEqual(y2c.shape, (len(fieldIdx), len(getZn3Idx)))

        fieldIdx = []
        y2c = self.optStateEstiData.getY2Corr(fieldIdx)
        self.assertEqual(len(y2c), 0)

    def testGetY2CorrWithIncompleteIdx(self):

        zn3Idx = np.arange(3, 9)
        dofIdx = np.arange(1, 40, 3)
        self.optStateEstiData.setZkAndDofIdxArrays(zn3Idx, dofIdx)

        fieldIdx = [1, 2, 3]
        y2c = self.optStateEstiData.getY2Corr(fieldIdx)
        self.assertEqual(y2c.shape, (len(fieldIdx), len(zn3Idx)))

    def testGetIntrinsicZk(self):

        fieldIdx = [1, 2, 3]
        activeFilter = FilterType.REF
        intrinsicZk = self.optStateEstiData.getIntrinsicZk(activeFilter,
                                                           fieldIdx)

        zn3Idx = self.optStateEstiData.getZn3Idx()
        self.assertEqual(intrinsicZk.shape, (len(fieldIdx), len(zn3Idx)))

        ans = -2.9368E-002 * self.optStateEstiData.getEffWave(activeFilter)
        self.assertEqual(intrinsicZk[1][2], ans)

        activeFilter = FilterType.G
        intrinsicZk = self.optStateEstiData.getIntrinsicZk(activeFilter,
                                                           fieldIdx)
        ans = -2.9422E-002 * self.optStateEstiData.getEffWave(activeFilter)
        self.assertEqual(intrinsicZk[1][2], ans)

        fieldIdx = []
        intrinsicZk = self.optStateEstiData.getIntrinsicZk(activeFilter,
                                                           fieldIdx)
        self.assertEqual(len(intrinsicZk), 0)

    def testGetIntrinsicZkWithIncompleteIdx(self):

        zn3Idx = np.arange(3, 9)
        dofIdx = np.arange(1, 40, 3)
        self.optStateEstiData.setZkAndDofIdxArrays(zn3Idx, dofIdx)

        fieldIdx = [1, 2, 3]
        activeFilter = FilterType.REF
        intrinsicZk = self.optStateEstiData.getIntrinsicZk(activeFilter,
                                                           fieldIdx)
        self.assertEqual(intrinsicZk.shape, (len(fieldIdx), len(zn3Idx)))

        ans = 3.8937E-006 * self.optStateEstiData.getEffWave(activeFilter)
        self.assertEqual(intrinsicZk[1][2], ans)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
