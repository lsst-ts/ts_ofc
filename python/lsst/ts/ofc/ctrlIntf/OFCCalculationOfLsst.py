from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculation import OFCCalculation
from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN


class OFCCalculationOfLsst(OFCCalculation):
    """The concrete child class of OFCCalculation of the LSST."""

    def __init__(self):
        super(OFCCalculationOfLsst, self).__init__(FWHMToPSSN(), InstName.LSST)


if __name__ == "__main__":
    pass
