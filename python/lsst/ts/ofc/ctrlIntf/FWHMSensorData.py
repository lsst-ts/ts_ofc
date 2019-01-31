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

        self.sensorId = None
        self.fwhmValues = None

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

        if (sensorId < 0):
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
