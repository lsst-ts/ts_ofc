import os
import numpy as np
import unittest

from lsst.ts.wep.Utility import FilterType
from lsst.ts.wep.ctrlIntf.SensorWavefrontError import SensorWavefrontError

from lsst.ts.ofc.Utility import InstName, getModulePath
from lsst.ts.ofc.ctrlIntf.FWHMSensorData import FWHMSensorData
from lsst.ts.ofc.ctrlIntf.OFCCalculationFactory import OFCCalculationFactory
from lsst.ts.ofc.IterDataReader import IterDataReader


class TestIteration(unittest.TestCase):
    """Test the iteration."""

    def setUp(self):

        self.ofc = OFCCalculationFactory.getCalculator(InstName.COMCAM)
        self.ofc.setFilter(FilterType.REF)
        self.ofc.setRotAng(0.0)
        self.ofc.setGainByPSSN()

        iterDataDir = os.path.join(getModulePath(), "tests", "testData",
                                   "iteration", "comcam")
        self.iterDataReader = IterDataReader(iterDataDir)

    def testIteration(self):

        wfIdList = self.iterDataReader.getSensorIdListComCam()
        fwhmIdList = self.iterDataReader.getPssnSensorIdListComCam()

        numOfFwhm = 9

        maxIterNum = 5
        for iterNum in range(0, maxIterNum):

            # Simulate to get the FWHM data from DM
            fwhmValues = self.iterDataReader.getFwhm(iterNum, numOfFwhm)
            listOfFWHMSensorData = self._getListOfFWHMSensorData(fwhmIdList,
                                                                 fwhmValues)

            # Set the FWHM data
            self.ofc.setFWHMSensorDataOfCam(listOfFWHMSensorData)

            # Simulate to get the WF sensor data from WEP
            wfErrValues = self.iterDataReader.getWfsErr(iterNum)
            listOfWfErr = self._getListOfSensorWavefrontError(wfIdList,
                                                              wfErrValues)

            # Calculate the subsystem correction
            m2HexapodCorrection, hexapodCorrection, m1m3Correction, m2Correction = \
                self.ofc.calculateCorrections(listOfWfErr)

            # Assert the correction by the length only
            self.assertEqual(len(m2HexapodCorrection.getCorrection()), 6)
            self.assertEqual(len(hexapodCorrection.getCorrection()), 6)
            self.assertEqual(len(m1m3Correction.getZForces()), 156)
            self.assertEqual(len(m2Correction.getZForces()), 72)

            # Get the aggregated state
            stateAgg = self.ofc.getStateAggregated()

            # Read the answer of DOF in the test file. The calculated DOF
            # is applied to the next iteration/ visit.
            dofAns = self.iterDataReader.getDof(iterNum)

            delta = np.sum(np.abs(stateAgg - dofAns))
            self.assertLess(delta, 0.002)

    def _getListOfFWHMSensorData(self, fwhmIdList, fwhmValues):

        listOfFWHMSensorData = []
        for fwhmId, fwhm in zip(fwhmIdList, fwhmValues):
            fwhmSensorData = FWHMSensorData(fwhmId, np.array([fwhm]))
            listOfFWHMSensorData.append(fwhmSensorData)

        return listOfFWHMSensorData

    def _getListOfSensorWavefrontError(self, wfIdList, wfErrValues):

        listOfWfErr = []
        for wfId, wfErr in zip(wfIdList, wfErrValues):
            sensorWavefrontError = SensorWavefrontError(numOfZk=19)
            sensorWavefrontError.setSensorId(wfId)
            sensorWavefrontError.setAnnularZernikePoly(wfErr)

            listOfWfErr.append(sensorWavefrontError)

        return listOfWfErr


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
