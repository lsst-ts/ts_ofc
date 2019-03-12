import os
import numpy as np
import unittest

from lsst.ts.wep.Utility import FilterType

from lsst.ts.ofc.Utility import InstName, getModulePath, getConfigDir
from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator
from lsst.ts.ofc.OptStateEsti import OptStateEsti


class TestOptStateEsti(unittest.TestCase):
    """Test the OptStateEsti class."""

    def setUp(self):

        dataShare = DataShare()
        configDir = getConfigDir()
        dataShare.config(configDir, instName=InstName.LSST)

        self.optStateEstiData = OptStateEstiDataDecorator(dataShare)
        self.optStateEstiData.configOptStateEstiData()

        self.optStateEsti = OptStateEsti()

        wfsFilePath = os.path.join(getModulePath(), "tests", "testData",
                                   "lsst_wfs_error_iter0.z4c")
        sensorNameList = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]
        wfErr, fieldIdx = self.optStateEstiData.getWfAndFieldIdFromFile(
            wfsFilePath, sensorNameList)
        self.wfErr = wfErr
        self.fieldIdx = fieldIdx

    def testEstiOptState(self):

        optState = self.optStateEsti.estiOptState(self.optStateEstiData,
                                                  FilterType.REF, self.wfErr,
                                                  self.fieldIdx)
        dofIdx = self.optStateEstiData.getDofIdx()

        self.assertEqual(len(optState), len(dofIdx))
        self.assertAlmostEqual(optState[0], 13.9943858)
        self.assertAlmostEqual(optState[1], 0.0303436526)
        self.assertAlmostEqual(optState[2], -0.0360475823)

    def testEstiOptStateWithDifferentZkIdxAndDofIdx(self):

        zn3Idx = np.arange(5)
        dofIdx = np.arange(10)
        self.optStateEstiData.setZkAndDofIdxArrays(zn3Idx, dofIdx)

        optState = self.optStateEsti.estiOptState(self.optStateEstiData,
                                                  FilterType.REF, self.wfErr,
                                                  self.fieldIdx)
        self.assertEqual(len(optState), len(dofIdx))
        self.assertAlmostEqual(optState[0], -645.7540849494324)
        self.assertAlmostEqual(optState[1], -10221.082801186029)
        self.assertAlmostEqual(optState[2], -758.518174)

    def testEstiOptStateWithoutEnoughZk(self):

        zn3Idx = np.arange(4)
        dofIdx = np.arange(20)
        self.optStateEstiData.setZkAndDofIdxArrays(zn3Idx, dofIdx)

        self.assertRaises(RuntimeError, self.optStateEsti.estiOptState,
                          self.optStateEstiData, FilterType.REF, self.wfErr,
                          self.fieldIdx)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
