class FWHMToPSSN(object):
    """Base class for converting FWHM data provided by DM to PSSN data 
    utilized by OFC.

    Nominally the final implementation will be provided by SE.
    """
    def __init__(self):
        super().__init__()

    def convertToPssn(self, fwhm):
        """Convert the FWHM data to PSSN.

        Take the array of FWHM values (nominally 1 per CCD) and convert
        it to PSSN (nominally 1 per CCD).

        Parameters
        ----------
        fwhm : numpy.ndarray[x]
            An array of FWHM values with sensor information.

        Returns
        -------
        numpy.ndarray[y]
            An array of PSSN values.
        """
        return [0.0] * len(fwhm)


if __name__ == "__main__":
    pass
