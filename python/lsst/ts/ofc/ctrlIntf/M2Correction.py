import numpy as np


class M2Correction(object):
    """Contains the correction for MT M2.
    """

    def __init__(self, zForces):
        """Construct a M2 correction.

        Parameters
        ----------
        zForces : numpy.ndarray[72] (float)
            The forces to apply to the 72 axial actuators in N.
        """

        self.zForces = np.zeros(72)

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

        if (len(zForces) != 72):
            raise ValueError("zForces must be an array of 72 floats.")
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
