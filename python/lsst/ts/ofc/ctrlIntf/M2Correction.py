import numpy as np


class M2Correction(object):
    """Contains the correction for MT M2."""

    NUM_OF_ACT = 72

    def __init__(self, zForces):
        """Construct a M2 correction.

        Parameters
        ----------
        zForces : numpy.ndarray[72] (float)
            The forces to apply to the 72 axial actuators in N.
        """

        self.zForces = np.zeros(self.NUM_OF_ACT)
        self.setZForces(zForces)

    def setZForces(self, zForces):
        """Set the M2 zForces.

        Parameters
        ----------
        zForces : numpy.ndarray[72] (float)
            The forces to apply to the 72 axial actuators in N.

        Raises
        ------
        ValueError
            zForces must be an array of 72 floats.
        """

        if (len(zForces) != self.NUM_OF_ACT):
            raise ValueError("zForces must be an array of %d floats."
                             % self.NUM_OF_ACT)
        self.zForces = zForces

    def getZForces(self):
        """Get the M2 zForces.

        Returns
        -------
        numpy.ndarray[72] (float)
            The forces to apply to the 72 axial actuators in N.
        """

        return self.zForces


if __name__ == "__main__":
    pass
