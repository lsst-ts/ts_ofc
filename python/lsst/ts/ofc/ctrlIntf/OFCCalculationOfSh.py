from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfIota import OFCCalculationOfIota


class OFCCalculationOfSh(OFCCalculationOfIota):
    """The concrete child class of OFCCalculation of the Shack-Hartmann"""

    def __init__(self):
        """Construct an OFC calculation of S.H. camera.

        S.H.: Shack-Hartmann.
        """

        # Use the data in ComCam
        super(OFCCalculationOfSh, self).__init__(InstName.COMCAM, "sh")


if __name__ == "__main__":
    pass
