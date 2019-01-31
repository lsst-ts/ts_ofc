from lsst.ts.ofc.ctrlIntf.OFCCalculation import OFCCalculation
from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN


class OFCCalculationOfComCam(OFCCalculation):
    """The concrete child class of OFCCalculation of the ComCam"""

    def __init__(self, fwhmToPssn):
        super(OFCCalculationOfComCam, self).__init__(FWHMToPSSN())


if __name__ == "__main__":
    pass
