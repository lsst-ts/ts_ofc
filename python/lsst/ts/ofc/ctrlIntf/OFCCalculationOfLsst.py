from lsst.ts.ofc.ctrlIntf.OFCCalculation import OFCCalculation
from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN


class OFCCalculationOfLsst(OFCCalculation):
    """The concrete child class of OFCCalculation of the LSST."""

    def __init__(self, fwhmToPssn):
        super(OFCCalculationOfLsst, self).__init__(FWHMToPSSN())


if __name__ == "__main__":
    pass
