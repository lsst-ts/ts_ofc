# This file is part of ts_ofc.
#
# Developed for the LSST Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
