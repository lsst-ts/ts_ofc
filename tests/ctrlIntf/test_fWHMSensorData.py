import unittest
import numpy as np

from lsst.ts.ofc.ctrlIntf.FWHMSensorData import FWHMSensorData


class TestFWHMSensorData(unittest.TestCase):
    """Test the FWHMSensorData class."""

    def setUp(self):

        self.sensorId = 1
        self.fwhmValues = np.ones(3)
        self.fwhmSensorData = FWHMSensorData(self.sensorId, self.fwhmValues)

    def testGetSensorId(self):

        sensorId = self.fwhmSensorData.getSensorId()
        self.assertEqual(sensorId, self.sensorId)

    def testSetSensorId(self):

        sensorId = 3
        self.fwhmSensorData.setSensorId(sensorId)

        sensorIdInFwhmSensorData = self.fwhmSensorData.getSensorId()
        self.assertEqual(sensorIdInFwhmSensorData, sensorId)

    def testSetSensorIdWithWrongValue(self):

        sensorId = -1
        self.assertRaises(ValueError, self.fwhmSensorData.setSensorId, sensorId)

    def testGetFwhmValues(self):

        fwhm = self.fwhmSensorData.getFwhmValues()

        delta = np.sum(np.abs(fwhm - self.fwhmValues))
        self.assertEqual(delta, 0)

        self.assertTrue(isinstance(fwhm, np.ndarray))

    def testSetFwhmValues(self):

        fwhm = np.ones(10)
        self.fwhmSensorData.setFwhmValues(fwhm)

        fwhmInFWHMSensorData = self.fwhmSensorData.getFwhmValues()
        delta = np.sum(np.abs(fwhm - fwhmInFWHMSensorData))
        self.assertEqual(delta, 0)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
