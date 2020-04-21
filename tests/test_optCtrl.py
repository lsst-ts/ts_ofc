import os
import numpy as np
import unittest

from lsst.ts.wep.Utility import FilterType

from lsst.ts.ofc.Utility import InstName, getModulePath, getConfigDir
from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator
from lsst.ts.ofc.OptStateEsti import OptStateEsti
from lsst.ts.ofc.OptCtrl import OptCtrl


class TestOptCtrl(unittest.TestCase):
    """Test the OptCtrl class."""

    def setUp(self):

        dataShare = DataShare()
        configDir = getConfigDir()
        dataShare.config(configDir, instName=InstName.LSST)

        optStateEstiData = OptStateEstiDataDecorator(dataShare)
        optStateEstiData.configOptStateEstiData()
        self.mixedData = OptCtrlDataDecorator(optStateEstiData)
        self.mixedData.configOptCtrlData()

        optStateEsti = OptStateEsti()
        wfsFilePath = os.path.join(getModulePath(), "tests", "testData",
                                   "lsst_wfs_error_iter0.z4c")
        sensorNameList = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]
        wfErr, fieldIdx = optStateEstiData.getWfAndFieldIdFromFile(
            wfsFilePath, sensorNameList)

        self.filterType = FilterType.REF
        self.optSt = optStateEsti.estiOptState(optStateEstiData,
                                               self.filterType, wfErr,
                                               fieldIdx)

        self.optCtrl = OptCtrl()

        state0InDof = self.mixedData.getState0FromFile()
        testState0InDof = np.ones(len(state0InDof))
        self.optCtrl.setState0(testState0InDof)
        self.optCtrl.initStateToState0()

    def testEstiUkWithoutGainWithX0(self):

        self.mixedData.xRef = "x0"
        uk = self.optCtrl.estiUkWithoutGain(self.mixedData, self.filterType,
                                            self.optSt)

        self.assertEqual(len(uk), len(self.mixedData.getDofIdx()))
        self.assertAlmostEqual(uk[0], -9.45590577, places=7)
        self.assertAlmostEqual(uk[1], -2.53901017, places=7)
        self.assertAlmostEqual(uk[2], -0.53020684, places=7)

    def testEstiUkWithoutGainWith0(self):

        self.mixedData.xRef = "0"
        uk = self.optCtrl.estiUkWithoutGain(self.mixedData, self.filterType,
                                            self.optSt)

        self.assertEqual(len(uk), len(self.mixedData.getDofIdx()))
        self.assertAlmostEqual(uk[0], -14.43967495, places=7)
        self.assertAlmostEqual(uk[1], -24.74416213, places=7)
        self.assertAlmostEqual(uk[2], 97.38850800, places=7)

    def testEstiUkWithoutGainWithX00(self):

        self.mixedData.xRef = "x00"
        uk = self.optCtrl.estiUkWithoutGain(self.mixedData, self.filterType,
                                            self.optSt)

        self.assertEqual(len(uk), len(self.mixedData.getDofIdx()))
        self.assertAlmostEqual(uk[0], -9.45590577, places=7)
        self.assertAlmostEqual(uk[1], -2.53901017, places=7)
        self.assertAlmostEqual(uk[2], -0.53020684, places=7)

    def testEstiUkWithoutGainAndXref(self):

        self.mixedData.xRef = None
        self.assertRaises(ValueError, self.optCtrl.estiUkWithoutGain,
                          self.mixedData, self.filterType, self.optSt)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
