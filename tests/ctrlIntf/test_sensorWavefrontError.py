import unittest
import numpy as np

from lsst.ts.ofc.ctrlIntf.SensorWavefrontError import SensorWavefrontError


class TestSensorWavefrontError(unittest.TestCase):
    """Test the SensorWavefrontError class."""

    def setUp(self):

        self.numOfZk = SensorWavefrontError.NUM_OF_ZK

        self.sensorId = 1
        self.annularZernikePoly = np.ones(self.numOfZk)
        self.sensorWavefrontError = SensorWavefrontError(
            self.sensorId, self.annularZernikePoly)

    def testGetSensorId(self):

        sensorId = self.sensorWavefrontError.getSensorId()
        self.assertEqual(sensorId, self.sensorId)
        self.assertTrue(isinstance(sensorId, int))

    def testSetSensorId(self):

        sensorId = 2
        self.sensorWavefrontError.setSensorId(sensorId)

        sensorIdInObject = self.sensorWavefrontError.getSensorId()
        self.assertEqual(sensorIdInObject, sensorId)

    def testSetSensorIdWithFloatInputType(self):

        sensorId = 2.0
        self.sensorWavefrontError.setSensorId(sensorId)

        sensorIdInObject = self.sensorWavefrontError.getSensorId()
        self.assertTrue(isinstance(sensorIdInObject, int))
        self.assertEqual(sensorIdInObject, sensorId)

    def testSetSensorIdWithValueLessThanZero(self):

        self.assertRaises(ValueError, self.sensorWavefrontError.setSensorId,
                          -1)

    def testGetAnnularZernikePoly(self):

        annularZernikePoly = self.sensorWavefrontError.getAnnularZernikePoly()

        self.assertEqual(len(annularZernikePoly), self.numOfZk)
        self.assertTrue(isinstance(annularZernikePoly, np.ndarray))

        delta = np.sum(np.abs(annularZernikePoly - self.annularZernikePoly))
        self.assertEqual(delta, 0)

    def testSetAnnularZernikePoly(self):

        randValue = np.random.rand(self.numOfZk)
        self.sensorWavefrontError.setAnnularZernikePoly(randValue)

        valueInObj = self.sensorWavefrontError.getAnnularZernikePoly()

        delta = np.sum(np.abs(randValue - valueInObj))
        self.assertEqual(delta, 0)

    def testSetAnnularZernikePolyWithListInput(self):

        listValue = [1] * self.numOfZk
        self.sensorWavefrontError.setAnnularZernikePoly(listValue)

        valueInObj = self.sensorWavefrontError.getAnnularZernikePoly()
        self.assertEqual(np.sum(valueInObj), self.numOfZk)

    def testSetAnnularZernikePolyWithWrongLength(self):

        wrongValue = np.ones(self.numOfZk+1)
        self.assertRaises(ValueError,
                          self.sensorWavefrontError.setAnnularZernikePoly,
                          wrongValue)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
