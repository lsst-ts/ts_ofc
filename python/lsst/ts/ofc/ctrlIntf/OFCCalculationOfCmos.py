from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfIota import OFCCalculationOfIota


class OFCCalculationOfCmos(OFCCalculationOfIota):
    """The concrete child class of OFCCalculation of the CMOS"""

    def __init__(self):
        """Construct an OFC calculation of CMOS camera.

        CMOS: Complementary metal–oxide–semiconductor.
        """

        # Use the data in ComCam
        super(OFCCalculationOfCmos, self).__init__(InstName.COMCAM, "cmos")


if __name__ == "__main__":
    pass
