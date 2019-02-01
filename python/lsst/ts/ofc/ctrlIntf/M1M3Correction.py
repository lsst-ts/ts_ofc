import numpy as np


class M1M3Correction(object):
    """Contains the correction for MT M1M3."""

    NUM_OF_ACT = 156

    def __init__(self, zForces):
        """Construct a M1M3 correction.

        Parameters
        ----------
        zForces : numpy.ndarray[156] (float)
            The forces to apply to the 156 force actuators in N.
        """

        self.zForces = np.zeros(self.NUM_OF_ACT)
        self.setZForces(zForces)

    def setZForces(self, zForces):
        """Set the M1M3 z force correction.

        Parameters
        ----------
        zForces : numpy.ndarray[156] (float)
            The forces to apply to the 156 force actuators in N.

        Raises
        ------
        ValueError
            zForces must be an array of 156 floats.
        """

        if (len(zForces) != self.NUM_OF_ACT):
            raise ValueError("zForces must be an array of %d floats."
                             % self.NUM_OF_ACT)
        self.zForces = zForces

    def getZForces(self):
        """Get the M1M3 z force correction.

        Returns
        -------
        numpy.ndarray[156] (float)
            The forces to apply to the 156 force actuators in N.
        """

        return self.zForces


if __name__ == "__main__":
    pass
