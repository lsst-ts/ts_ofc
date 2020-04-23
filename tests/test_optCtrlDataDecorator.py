import numpy as np
import unittest

from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator
from lsst.ts.ofc.Utility import InstName, getConfigDir


class TestOptCtrlDataDecorator(unittest.TestCase):
    """Test the OptCtrlDataDecorator class."""

    def setUp(self):

        dataShare = DataShare()
        configDir = getConfigDir()
        dataShare.config(configDir, instName=InstName.LSST)
        self.optCtrlData = OptCtrlDataDecorator(dataShare)
        self.optCtrlData.configOptCtrlData()

    def testGetAuthority(self):

        authority = self.optCtrlData.getAuthority()
        self.assertEqual(len(authority), 50)
        self.assertAlmostEqual(authority[0], 1, places=7)
        self.assertAlmostEqual(authority[1], 0.88059701, places=7)
        self.assertAlmostEqual(authority[11], 98.67768094, places=7)
        self.assertAlmostEqual(authority[12], 411.52843713, places=7)
        self.assertAlmostEqual(authority[31], 40.09005230, places=7)
        self.assertAlmostEqual(authority[32], 286.99711319, places=7)

    def testGetQwgt(self):

        qWgt = self.optCtrlData.getQwgt()
        self.assertEqual(len(qWgt), 31)
        self.assertAlmostEqual(np.sum(qWgt), 1, places=7)
        self.assertAlmostEqual(qWgt[1], 0.01974265, places=7)

    def testGetQwgtOfComcam(self):

        dataShare = DataShare()
        configDir = getConfigDir()
        dataShare.config(configDir, instName=InstName.COMCAM)
        optCtrlData = OptCtrlDataDecorator(dataShare)
        optCtrlData.configOptCtrlData()

        qWgt = optCtrlData.getQwgt()
        self.assertEqual(len(qWgt), 9)
        self.assertAlmostEqual(np.sum(qWgt), 1, places=7)

    def testGetPssnAlpha(self):

        pssnAlpha = self.optCtrlData.getPssnAlpha()
        self.assertTrue(isinstance(pssnAlpha, np.ndarray))
        self.assertEqual(len(pssnAlpha), 19)
        self.assertEqual(pssnAlpha[0], 6.6906168e-03)

    def testGetNumOfFieldInQwgt(self):

        numOfField = self.optCtrlData.getNumOfFieldInQwgt()
        self.assertEqual(numOfField, 31)

    def testGetMotRng(self):

        motRng = self.optCtrlData.getMotRng()
        self.assertEqual(len(motRng), 50)
        self.assertEqual(motRng[0], 5900)

    def testGetState0FromFile(self):

        state0InDof = self.optCtrlData.getState0FromFile()
        self.assertEqual(len(state0InDof), 50)
        self.assertEqual(np.sum(state0InDof), 0)

    def testGetPenality(self):

        penality = self.optCtrlData.getPenality()
        self.assertEqual(penality["M1M3Act"], 13.2584)
        self.assertEqual(penality["M2Act"], 134)
        self.assertEqual(penality["Motion"], 0.001)

    def testGetXref(self):

        xRef = self.optCtrlData.getXref()
        self.assertEqual(xRef, "x00")


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
