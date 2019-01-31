class M2HexapodCorrection(object):
    """Contains the correction for MT M2 Hexapod.
    """

    def __init__(self, xTilt, yTilt, piston):
        """Construct a M2 Hexapod correction.

        Parameters
        ----------
        xTilt : float
            The X rotation offset in radians.
        yTilt : float
            The Y rotation offset in radians.
        piston : float
            THe Z position offset in um.
        """

        self.xTilt = 0.0
        self.yTilt = 0.0
        self.piston = 0.0

        self.setCorrection(xTilt, yTilt, piston)

    def setCorrection(self, xTilt, yTilt, piston):
        """Set the M2 hexapod correction.

        Parameters
        ----------
        xTilt : float
            The X rotation offset in radians.
        yTilt : float
            The Y rotation offset in radians.
        piston : float
            The Z position offset in um.
        """

        self.xTilt = xTilt
        self.yTilt = yTilt
        self.piston = piston

    def getCorrection(self):
        """Get the M2 hexapod correction.

        Returns
        -------
        float
            The X rotation offset in radians.
        float
            The Y rotation offset in radians.
        float
            The Z position offset in um.
        """

        return self.xTilt, self.yTilt, self.piston


if __name__ == "__main__":
    pass
