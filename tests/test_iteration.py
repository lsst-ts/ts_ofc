import os
import numpy as np
import unittest

from lsst.ts.wep.Utility import FilterType

from lsst.ts.ofc.Utility import InstName, DofGroup, getModulePath, getConfigDir
from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator
from lsst.ts.ofc.OptStateEsti import OptStateEsti
from lsst.ts.ofc.OptCtrl import OptCtrl
from lsst.ts.ofc.ZTAAC import ZTAAC
from lsst.ts.ofc.CamRot import CamRot
from lsst.ts.ofc.IterDataReader import IterDataReader


class TestIteration(unittest.TestCase):
    """Test the iteration."""

    def setUp(self):

        self.iterDataDir = os.path.join(getModulePath(), "tests", "testData",
                                        "iteration", "comcam")
        self.iterDataReader = IterDataReader(self.iterDataDir)

    def testSetDataDir(self):

        self.assertEqual(self.iterDataReader.dataDir, self.iterDataDir)

    def testGetAbsFilePathOfWfsErr(self):

        iterNum = 1
        filePath = self.iterDataReader.getAbsFilePathOfWfsErr(iterNum)

        self.assertTrue(os.path.exists(filePath))

    def testGetWfsErr(self):

        iterNum = 1
        wfsErr = self.iterDataReader.getWfsErr(iterNum)

        self.assertEqual(wfsErr.shape, (9, 19))

    def testGetPssn(self):

        iterNum = 1
        numOfPssn = 9
        pssn = self.iterDataReader.getPssn(iterNum, numOfPssn)

        self.assertEqual(len(pssn), 9)
        self.assertAlmostEqual(pssn[3], 0.92950413, places=7)

    def testGetFwhm(self):

        iterNum = 1
        numOfFwhm = 9
        fwhm = self.iterDataReader.getFwhm(iterNum, numOfFwhm)

        self.assertEqual(len(fwhm), 9)
        self.assertAlmostEqual(fwhm[3], 0.17944742, places=7)

    def testGetDof(self):

        iterNum = 1
        dof = self.iterDataReader.getDof(iterNum)

        self.assertEqual(len(dof), 50)
        self.assertAlmostEqual(dof[3], -1.26663684, places=7)

    def testGetSensorIdListWfs(self):

        sensorIdList = self.iterDataReader.getSensorIdListWfs()
        self.assertEqual(len(sensorIdList), 4)

    def testGetSensorIdListComCam(self):

        sensorIdList = self.iterDataReader.getSensorIdListComCam()
        self.assertEqual(len(sensorIdList), 9)

    def testGetPssnSensorIdListWfs(self):

        pssnIdList = self.iterDataReader.getPssnSensorIdListWfs()
        self.assertEqual(len(pssnIdList), 31)

    def testGetPssnSensorIdListComCam(self):

        pssnIdList = self.iterDataReader.getPssnSensorIdListComCam()
        self.assertEqual(len(pssnIdList), 9)

    def testIterationComCam(self):
        """Test the iteration of active optics closed-loop calculation of
        ComCam.

        This test relies on test data from a successful simulation run.
        """

        ztaac, camRot = self._prepareZtaac(InstName.COMCAM)

        sensorIdList = self.iterDataReader.getSensorIdListComCam()
        sensorNameList = ztaac.mapSensorIdToName(sensorIdList)[0]

        pssnIdList = self.iterDataReader.getPssnSensorIdListComCam()
        pssnSensorNameList = ztaac.mapSensorIdToName(pssnIdList)[0]

        numOfPssn = 9

        maxIterNum = 5
        for iterNum in range(0, maxIterNum):

            pssn = self.iterDataReader.getPssn(iterNum, numOfPssn)
            ztaac.setGainByPSSN(pssn, pssnSensorNameList)

            wfErr = self.iterDataReader.getWfsErr(iterNum)
            uk = ztaac.estiUkWithGain(wfErr, sensorNameList)

            rotUk = ztaac.rotUk(camRot, uk)
            ztaac.aggState(rotUk)

            # Collect the DOF for the comparison
            dof = []
            for dofGroup in DofGroup:
                # Get the DOF for each group
                dofOfGroup = ztaac.getGroupDof(dofGroup)
                dof = np.append(dof, dofOfGroup)
            dof += ztaac.getState0()

            # Read the answer of DOF in the test file. The calculated DOF
            # is applied to the next iteration/ visit.
            dofAns = self.iterDataReader.getDof(iterNum)

            delta = np.sum(np.abs(dof - dofAns))
            self.assertLess(delta, 0.002)

    def _prepareZtaac(self, instName):

        dataShare = DataShare()
        configDir = getConfigDir()
        dataShare.config(configDir, instName=instName)

        optStateEstiData = OptStateEstiDataDecorator(dataShare)
        optStateEstiData.configOptStateEstiData()

        mixedData = OptCtrlDataDecorator(optStateEstiData)
        mixedData.configOptCtrlData()

        optStateEsti = OptStateEsti()
        optCtrl = OptCtrl()

        ztaac = ZTAAC(optStateEsti, optCtrl, mixedData)
        ztaac.config(filterType=FilterType.REF, defaultGain=0.7,
                     fwhmThresholdInArcsec=0.2)

        ztaac.setState0FromFile(state0InDofFileName="state0inDof.yaml")
        ztaac.setStateToState0()

        camRot = CamRot()
        camRot.setRotAng(0)

        return ztaac, camRot


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
