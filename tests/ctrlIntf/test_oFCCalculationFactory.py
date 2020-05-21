import unittest

from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationFactory import OFCCalculationFactory
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfLsst import OFCCalculationOfLsst
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfComCam import OFCCalculationOfComCam
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfSh import OFCCalculationOfSh
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfCmos import OFCCalculationOfCmos


class TestOFCCalculationFactory(unittest.TestCase):
    """Test the OFCCalculationFactory class."""

    def setUp(self):
        self.state0Dof = {
            "M2Hexapod": {"dZ": 0, "dX": 0, "dY": 0, "rX": 0, "rY": 0},
            "cameraHexapod": {"dZ": 0, "dX": 0, "dY": 0, "rX": 0, "rY": 0},
            "M1M3Bending": {
                "mode1": 0,
                "mode2": 0,
                "mode3": 0,
                "mode4": 0,
                "mode5": 0,
                "mode6": 0,
                "mode7": 0,
                "mode8": 0,
                "mode9": 0,
                "mode10": 0,
                "mode11": 0,
                "mode12": 0,
                "mode13": 0,
                "mode14": 0,
                "mode15": 0,
                "mode16": 0,
                "mode17": 0,
                "mode18": 0,
                "mode19": 0,
                "mode20": 0,
            },
            "M2Bending": {
                "mode1": 0,
                "mode2": 0,
                "mode3": 0,
                "mode4": 0,
                "mode5": 0,
                "mode6": 0,
                "mode7": 0,
                "mode8": 0,
                "mode9": 0,
                "mode10": 0,
                "mode11": 0,
                "mode12": 0,
                "mode13": 0,
                "mode14": 0,
                "mode15": 0,
                "mode16": 0,
                "mode17": 0,
                "mode18": 0,
                "mode19": 0,
                "mode20": 0,
            },
        }

    def testGetCalculatorOfLsst(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.LSST)

        self.assertTrue(isinstance(calculator, OFCCalculationOfLsst))

    def testGetCalculatorOfLsstDoF(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.LSST, self.state0Dof)

        self.assertTrue(isinstance(calculator, OFCCalculationOfLsst))

    def testGetCalculatorOfComCam(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.COMCAM)

        self.assertTrue(isinstance(calculator, OFCCalculationOfComCam))

    def testGetCalculatorOfComCamDof(self):

        calculator = OFCCalculationFactory.getCalculator(
            InstName.COMCAM, self.state0Dof
        )

        self.assertTrue(isinstance(calculator, OFCCalculationOfComCam))

    def testGetCalculatorOfSh(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.SH)
        self.assertTrue(isinstance(calculator, OFCCalculationOfSh))

    def testGetCalculatorOfShDoF(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.SH, self.state0Dof)
        self.assertTrue(isinstance(calculator, OFCCalculationOfSh))

    def testGetCalculatorOfCmos(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.CMOS)
        self.assertTrue(isinstance(calculator, OFCCalculationOfCmos))

    def testGetCalculatorOfCmosDoF(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.CMOS, self.state0Dof)
        self.assertTrue(isinstance(calculator, OFCCalculationOfCmos))

    def testGetCalculatorOfWrongInst(self):

        self.assertRaises(ValueError, OFCCalculationFactory.getCalculator, "wrongInst")


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
