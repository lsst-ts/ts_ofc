class HexapodCorrection(object):
    """Contains the correction for MT Hexapod.
    """

    def __init__(self, x, y, z, u, v, w=0.0):
        """Construct a Hexapod correction.

        Parameters
        ----------
        x : float
            The X position offset in um.
        y : float
            The Y position offset in um.
        z : float
            The Z position offset in um.
        u : float
            The X rotation offset in deg.
        v : float
            The Y rotation offset in deg.
        w : float (optional)
            The Z rotation offset in deg. (the default is 0.0)
        """

        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.u = 0.0
        self.v = 0.0
        self.w = 0.0

        self.setCorrection(x, y, z, u, v, w)

    def setCorrection(self, x, y, z, u, v, w=0.0):
        """Set the hexapod correction.

        Parameters
        ----------
        x : float
            The X position offset in um.
        y : float
            The Y position offset in um.
        z : float
            The Z position offset in um.
        u : float
            The X rotation offset in deg.
        v : float
            The Y rotation offset in deg.
        w : float, optional
            The Z rotation offset in deg. (the default is 0.0.)
        """

        self.x = x
        self.y = y
        self.z = z
        self.u = u
        self.v = v
        self.w = w

    def getCorrection(self):
        """Get the hexapod correction.

        Returns
        -------
        float
            The X position offset in um.
        float
            The Y position offset in um.
        float
            The Z position offset in um.
        float
            The X rotation offset in deg.
        float
            The Y rotation offset in deg.
        float
            The Z rotation offset in deg.
        """

        return self.x, self.y, self.z, self.u, self.v, self.w 


if __name__ == "__main__":
    pass
