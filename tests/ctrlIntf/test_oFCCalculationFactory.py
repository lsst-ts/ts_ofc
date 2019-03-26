import unittest

from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationFactory import OFCCalculationFactory
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfLsst import OFCCalculationOfLsst
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfComCam import OFCCalculationOfComCam
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfSh import OFCCalculationOfSh
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfCmos import OFCCalculationOfCmos


class TestOFCCalculationFactory(unittest.TestCase):
    """Test the OFCCalculationFactory class."""

    def testGetCalculatorOfLsst(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.LSST)

        self.assertTrue(isinstance(calculator, OFCCalculationOfLsst))

    def testGetCalculatorOfComCam(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.COMCAM)

        self.assertTrue(isinstance(calculator, OFCCalculationOfComCam))

    def testGetCalculatorOfSh(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.SH)
        self.assertTrue(isinstance(calculator, OFCCalculationOfSh))

    def testGetCalculatorOfCmos(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.CMOS)
        self.assertTrue(isinstance(calculator, OFCCalculationOfCmos))

    def testGetCalculatorOfWrongInst(self):

        self.assertRaises(ValueError, OFCCalculationFactory.getCalculator,
                          "wrongInst")


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
