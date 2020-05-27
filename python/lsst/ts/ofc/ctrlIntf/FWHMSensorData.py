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

import numpy as np


class FWHMSensorData(object):
    """Contains the FWHM data for a sensor."""

    def __init__(self, sensorId, fwhmValues):
        """Construct a FWHMSensorData class.

        Parameters
        ----------
        sensorId : int
            The sensor id these FWHM values apply to.
        fwhmValues : numpy.ndarray[x]
            The FWHM values for this sensor.
        """

        self.sensorId = 0
        self.fwhmValues = np.array([])

        self.setSensorId(sensorId)
        self.setFwhmValues(fwhmValues)

    def setSensorId(self, sensorId):
        """Set the sensor Id.

        Parameters
        ----------
        sensorId : int
            The sensor Id these FWHM values apply to.

        Raises
        ------
        ValueError
            sensorId must be >= 0.
        """

        if sensorId < 0:
            raise ValueError("sensorId must be >= 0.")

        self.sensorId = sensorId

    def getSensorId(self):
        """Get the sensor Id.

        Returns
        -------
        int
            The sensor id these FWHM values apply to.
        """

        return self.sensorId

    def setFwhmValues(self, fwhmValues):
        """Set the FWHM values.

        Parameters
        ----------
        fwhmValues : numpy.ndarray[x]
            The FWHM values for this sensor.
        """

        self.fwhmValues = fwhmValues

    def getFwhmValues(self):
        """Get the FWHM values.

        Returns
        -------
        numpy.ndarray[x]
            The FWHM values for this sensor.
        """

        return self.fwhmValues


if __name__ == "__main__":
    pass
