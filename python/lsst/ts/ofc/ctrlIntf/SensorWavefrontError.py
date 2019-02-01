import numpy as np


class SensorWavefrontError(object):
    """Contains the wavefront errors for a single sensor."""

    NUM_OF_ZER = 19

    def __init__(self, sensorId, annularZernikePoly):
        """Constructs a sensor wavefront error.

        Parameters
        ----------
        sensorId : int
            The Id of the sensor this wavefront error is for.
        annularZernikePoly : numpy.ndarray[19] (float)
            The poly describing the wavefront error.
        """

        self.sensorId = 0
        self.annularZernikePoly = np.zeros(self.NUM_OF_ZER)

        self.setSensorId(sensorId)
        self.setAnnularZernikePoly(annularZernikePoly)

    def setSensorId(self, sensorId):
        """Set the sensor Id.

        Parameters
        ----------
        sensorId : int
            The Id of the sensor this wavefront error is for.

        Raises
        ------
        ValueError
            sensorId must be >= 0.
        """

        if (sensorId < 0):
            raise ValueError("sensorId must be >= 0.")
        self.sensorId = int(sensorId)

    def getSensorId(self):
        """Get the sensor Id.

        Returns
        -------
        int
            The Id of the sensor this wavefront error is for.
        """

        return self.sensorId

    def setAnnularZernikePoly(self, annularZernikePoly):
        """Set the annular zernike poly.

        Parameters
        ----------
        annularZernikePoly : numpy.ndarray[19] (float)
            The poly describing the wavefront error.

        Raises
        ------
        ValueError
            annularZernikePoly must be an array of 19 floats.
        """

        if (len(annularZernikePoly) != self.NUM_OF_ZER):
            raise ValueError("annularZernikePoly must be an array of %d floats."
                             % self.NUM_OF_ZER)
        self.annularZernikePoly = np.array(annularZernikePoly)

    def getAnnularZernikePoly(self):
        """Get the annular zernike poly.

        Returns
        -------
        numpy.ndarray[19] (float)
            The poly describing the wavefront error.
        """

        return self.annularZernikePoly


if __name__ == "__main__":
    pass
