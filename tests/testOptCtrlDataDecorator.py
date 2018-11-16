import os
import numpy as np
import unittest

from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator
from lsst.ts.ofc.Utility import InstName


class TestOptCtrlDataDecorator(unittest.TestCase):
    """Test the OptCtrlDataDecorator class."""

    def setUp(self):

        dataShare = DataShare()
        configDir = os.path.join("..", "configData")
        dataShare.config(configDir, instName=InstName.LSST)
        self.optCtrlData = OptCtrlDataDecorator(dataShare)
        self.optCtrlData.configOptCtrlData()

    def testGetAuthority(self):

        authority = self.optCtrlData.getAuthority()
        self.assertEqual(len(authority), 50)
        self.assertAlmostEqual(authority[0], 1)
        self.assertAlmostEqual(authority[1], 0.880597015)
        self.assertAlmostEqual(authority[11], 45.96449329039931)
        self.assertAlmostEqual(authority[12], 103.4589756080062)
        self.assertAlmostEqual(authority[31], 45.96449329039931)
        self.assertAlmostEqual(authority[32], 103.4589756080062)

    def testGetQwgtFromFile(self):

        qWgt = self.optCtrlData.getQwgtFromFile()
        self.assertEqual(len(qWgt), 31)
        self.assertAlmostEqual(np.sum(qWgt), 1)
        self.assertAlmostEqual(qWgt[1], 0.01974265)

    def testGetQwgtFromFileOfComcam(self):

        dataShare = DataShare()
        configDir = os.path.join("..", "configData")
        dataShare.config(configDir, instName=InstName.COMCAM)
        optCtrlData = OptCtrlDataDecorator(dataShare)
        optCtrlData.configOptCtrlData()

        qWgt = optCtrlData.getQwgtFromFile()
        self.assertEqual(len(qWgt), 9)
        self.assertAlmostEqual(np.sum(qWgt), 1)

    def testGetPssnAlphaFromFile(self):

        pssnAlpha = self.optCtrlData.getPssnAlphaFromFile()
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
        self.assertEqual(penality["M1M3Act"], 5.9)
        self.assertEqual(penality["M2Act"], 5.9)
        self.assertEqual(penality["Motion"], 0.001)

    def testGetXref(self):

        xRef = self.optCtrlData.getXref()
        self.assertEqual(xRef, "x00")


if __name__ == "__main__":

    # Run the unit test
    unittest.main()