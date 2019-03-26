from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculation import OFCCalculation
from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN


class OFCCalculationOfComCam(OFCCalculation):
    """The concrete child class of OFCCalculation of the ComCam"""

    def __init__(self):
        """Construct an OFC calculation of ComCam.

        ComCam: Commissioning camera.
        """
        super(OFCCalculationOfComCam, self).__init__(FWHMToPSSN(),
                                                     InstName.COMCAM)


if __name__ == "__main__":
    pass
