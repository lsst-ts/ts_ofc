from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfLsst import OFCCalculationOfLsst
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfComCam import OFCCalculationOfComCam


class OFCCalculationFactory(object):
    """Factory for creating the correct OFC calculation based off the
    instrument currently being used.
    """

    def __init__(self):
        super().__init__()

    def getCalculator(self, instName):
        """Get a calculator to process wavefront error.

        Parameters
        ----------
        instName : InstName
            The instrument to get the wavefront calculator for.

        Returns
        -------
        OFCCalculationOfLsst or OFCCalculationOfComCam
            Concrete child class of OFCCalculation class.

        Raises
        ------
        ValueError
            This instrument is not supported.
        """

        if (instName == InstName.LSST):
            return OFCCalculationOfLsst()
        elif (instName == InstName.COMCAM):
            return OFCCalculationOfComCam()
        else:
            raise ValueError("This instrument is not supported.")


if __name__ == "__main__":
    pass
