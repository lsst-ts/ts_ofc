import os
import numpy as np
import unittest

from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator
from lsst.ts.ofc.Utility import InstName, getModulePath
from lsst.ts.ofc.OptCtrlDefault import OptCtrlDefault


class TestOptCtrlDefault(unittest.TestCase):
    """Test the OptCtrlDefault class."""

    def setUp(self):

        dataShare = DataShare()
        configDir = os.path.join(getModulePath(), "configData")
        dataShare.config(configDir, instName=InstName.LSST)
        self.optCtrlData = OptCtrlDataDecorator(dataShare)
        self.optCtrlData.configOptCtrlData()

        self.optCtrl = OptCtrlDefault()

    def testSetState0(self):

        state0 = [1, 2, 3, 4]
        self._assertDeltaState0IsZero(state0)

    def testSetState0WithEmptyInput(self):

        state0 = []
        self._assertDeltaState0IsZero(state0)

    def _assertDeltaState0IsZero(self, state0):

        self.optCtrl.setState0(state0)

        dofIdx = np.arange(len(state0))
        state0InOpCtrl = self.optCtrl.getState0(dofIdx)

        delta = np.sum(np.abs(state0InOpCtrl - np.array(state0)))
        self.assertEqual(delta, 0)

    def testSetState(self):

        state = [1, 2, 3, 4]
        self._assertDeltaStateIsZero(state)

    def testSetStateWithEmptyInput(self):

        state = []
        self._assertDeltaStateIsZero(state)

    def _assertDeltaStateIsZero(self, state):

        self.optCtrl.setState(state)

        dofIdx = np.arange(len(state))
        stateInOpCtrl = self.optCtrl.getState(dofIdx)

        delta = np.sum(np.abs(stateInOpCtrl - np.array(state)))
        self.assertEqual(delta, 0)

    def testInitStateToState0(self):

        state0 = [1, 2, 3, 4, 5]
        self.optCtrl.setState0(state0)
        self.optCtrl.initStateToState0()

        dofIdx = np.arange(len(state0))
        state0InOpCtrl = self.optCtrl.getState0(dofIdx)
        stateInOpCtrl = self.optCtrl.getState(dofIdx)

        delta = np.sum(np.abs(state0InOpCtrl - stateInOpCtrl))
        self.assertEqual(delta, 0)
        self.assertNotEqual(id(self.optCtrl.state0InDof),
                            id(self.optCtrl.stateInDof))

    def testGetNumOfState0(self):

        state0 = [1, 2, 3, 4, 5]
        self.optCtrl.setState0(state0)

        numOfState0 = self.optCtrl.getNumOfState0()
        self.assertEqual(numOfState0, len(state0))

    def testAggState(self):

        state0 = [1, 2, 3, 4, 5]
        self.optCtrl.setState0(state0)
        self.optCtrl.initStateToState0()

        calcDof = [1, 2, 3]
        dofIdx = [0, 2, 4]
        self.optCtrl.aggState(calcDof, dofIdx)

        ans = [2, 2, 5, 4, 8]
        stateInOpCtrl = self.optCtrl.getState(np.arange(len(state0)))
        delta = np.sum(np.abs(stateInOpCtrl - np.array(ans)))
        self.assertEqual(delta, 0)

    def testGetGroupDofWithInteralDof(self):

        state0 = [1, 2, 3, 4, 5]
        self.optCtrl.setState0(state0)

        state = [4, 1, 3, 2, 1]
        self.optCtrl.setState(state)

        startIdx = 1
        groupLeng = 2
        dof = self.optCtrl.getGroupDof(startIdx, groupLeng, inputDof=None)

        ans = [-1, 0]
        delta = np.sum(np.abs(dof - np.array(ans)))
        self.assertEqual(delta, 0)

    def testGetGroupDofWithInputDof(self):

        startIdx = 1
        groupLeng = 2
        inputDof = [4, 1, 3, 2, 1]
        dof = self.optCtrl.getGroupDof(startIdx, groupLeng, inputDof=inputDof)

        ans = [1, 3]
        delta = np.sum(np.abs(dof - np.array(ans)))
        self.assertEqual(delta, 0)

    def testSetAndGetGain(self):

        gain = 0.7
        self.optCtrl.setGain(gain)
        self.assertEqual(self.optCtrl.getGain(), gain)

    def testSetGainOutOfRange(self):

        gain = 1.9
        self.assertRaises(ValueError, self.optCtrl.setGain, gain)

    def testCalcEffGQFWHM(self):

        numOfFieldIdx = 31
        fieldIdx = np.arange(numOfFieldIdx)
        pssn = np.ones(numOfFieldIdx)*0.9

        fwhmGq = self.optCtrl.calcEffGQFWHM(self.optCtrlData, pssn, fieldIdx)
        self.assertEqual(fwhmGq, 0.2172)

    def testCalcEffGQFWHMwithPssnGreaterThanOne(self):

        numOfFieldIdx = 31
        fieldIdx = np.arange(numOfFieldIdx)
        pssn = np.ones(numOfFieldIdx)
        pssn[20] = 1.2

        self.assertRaises(ValueError, self.optCtrl.calcEffGQFWHM,
                          self.optCtrlData, pssn, fieldIdx)

    def testCalcEffGQFWHMwithPssnEqualsZero(self):

        numOfFieldIdx = 31
        fieldIdx = np.arange(numOfFieldIdx)
        pssn = np.ones(numOfFieldIdx)
        pssn[20] = 0

        self.assertRaises(ValueError, self.optCtrl.calcEffGQFWHM,
                          self.optCtrlData, pssn, fieldIdx)

    def testEstiUkWithGain(self):

        self.assertRaises(NotImplementedError,
                          self.optCtrl.estiUkWithGain,
                          None, None, None)

    def testEstiUkWithoutGain(self):

        self.assertRaises(NotImplementedError,
                          self.optCtrl.estiUkWithoutGain,
                          None, None, None)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
