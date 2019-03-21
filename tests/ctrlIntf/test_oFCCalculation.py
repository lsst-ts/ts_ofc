import unittest
import numpy as np

from lsst.ts.wep.Utility import FilterType

from lsst.ts.ofc.Utility import InstName

from lsst.ts.ofc.ctrlIntf.OFCCalculation import OFCCalculation
from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN
from lsst.ts.ofc.ctrlIntf.CameraHexapodCorrection import CameraHexapodCorrection
from lsst.ts.ofc.ctrlIntf.M2HexapodCorrection import M2HexapodCorrection
from lsst.ts.ofc.ctrlIntf.M1M3Correction import M1M3Correction
from lsst.ts.ofc.ctrlIntf.M2Correction import M2Correction
from lsst.ts.ofc.ctrlIntf.SensorWavefrontError import SensorWavefrontError
from lsst.ts.ofc.ctrlIntf.FWHMSensorData import FWHMSensorData


class TestOFCCalculation(unittest.TestCase):
    """Test the OFCCalculation class."""

    def setUp(self):

        self.ofcCalculation = OFCCalculation(FWHMToPSSN(), InstName.LSST)

    def testSetFWHMSensorDataOfCam(self):

        fwhmValues = np.ones(19) * 0.2
        numOfSensor = 5
        listOfFWHMSensorData = []
        for sglSensorId in range(numOfSensor):
            fwhmSensorData = FWHMSensorData(sglSensorId, fwhmValues)
            listOfFWHMSensorData.append(fwhmSensorData)

        self.ofcCalculation.setFWHMSensorDataOfCam(listOfFWHMSensorData)

        pssnData = self.ofcCalculation.getPssnData()
        sensorId = pssnData["sensorId"]
        pssn = pssnData["pssn"]

        self.assertEqual(sensorId.tolist(), list(range(numOfSensor)))
        self.assertAlmostEqual(pssn[0], 0.9139012)

    def testGetFilter(self):

        self.assertEqual(self.ofcCalculation.getFilter(), FilterType.REF)

    def testSetFilter(self):

        filterType = FilterType.R
        self.ofcCalculation.setFilter(filterType)

        self.assertEqual(self.ofcCalculation.getFilter(), filterType)

    def testGetRotAng(self):

        self.assertEqual(self.ofcCalculation.getRotAng(), 0.0)

    def testSetRotAng(self):

        rotAng = 10.0
        self.ofcCalculation.setRotAng(rotAng)

        self.assertEqual(self.ofcCalculation.getRotAng(), rotAng)

    def testResetOfcState(self):

        m2HexapodCorrection, hexapodCorrection, m1m3Correction, m2Correction = \
            self.ofcCalculation.resetOfcState()

        self.assertTrue(isinstance(m2HexapodCorrection, M2HexapodCorrection))
        self.assertTrue(isinstance(hexapodCorrection, CameraHexapodCorrection))
        self.assertTrue(isinstance(m1m3Correction, M1M3Correction))
        self.assertTrue(isinstance(m2Correction, M2Correction))

        self.assertEqual(np.sum(m2HexapodCorrection.getCorrection()), 0)
        self.assertEqual(np.sum(hexapodCorrection.getCorrection()), 0)
        self.assertEqual(np.sum(m1m3Correction.getZForces()), 0)
        self.assertEqual(np.sum(m2Correction.getZForces()), 0)

    def testSetGainByUser(self):

        self.assertEqual(self.ofcCalculation.useGainByPssn, True)
        self.assertEqual(self.ofcCalculation.getGainInUse(), 0.0)

        gainByUser = self._setGainByUser()
        self.assertEqual(self.ofcCalculation.useGainByPssn, False)
        self.assertEqual(self.ofcCalculation.getGainInUse(), gainByUser)

    def _setGainByUser(self):

        gainByUser = 0.5
        self.ofcCalculation.setGainByUser(gainByUser)

        return gainByUser

    def testSetGainByPSSN(self):

        self._setGainByUser()

        self.ofcCalculation.setGainByPSSN()
        self.assertEqual(self.ofcCalculation.useGainByPssn, True)

    def testCalculateCorrections(self):

        sensorIdList = [198, 31, 2, 169]
        annularZernikePoly = np.ones(19)
        listOfWfErr = []
        for sensorId in sensorIdList:
            sensorWavefrontError = SensorWavefrontError(sensorId,
                                                        annularZernikePoly)
            listOfWfErr.append(sensorWavefrontError)

        m2HexapodCorrection, hexapodCorrection, m1m3Correction, m2Correction = \
            self.ofcCalculation.calculateCorrections(listOfWfErr)

        self.assertTrue(isinstance(m2HexapodCorrection, M2HexapodCorrection))
        self.assertTrue(isinstance(hexapodCorrection, CameraHexapodCorrection))
        self.assertTrue(isinstance(m1m3Correction, M1M3Correction))
        self.assertTrue(isinstance(m2Correction, M2Correction))

    def testGetStateCorrectionFromLastVisit(self):

        stateCorrection = self.ofcCalculation.getStateCorrectionFromLastVisit()
        self.assertTrue(isinstance(stateCorrection, np.ndarray))
        self.assertEqual(len(stateCorrection),
                         self.ofcCalculation.ztaac.optCtrl.getNumOfState0())

    def testGetStateAggregated(self):

        stateAgg = self.ofcCalculation.getStateAggregated()
        self.assertTrue(isinstance(stateAgg, np.ndarray))
        self.assertEqual(len(stateAgg), 50)
        self.assertEqual(np.sum(np.abs(stateAgg)), 0)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
