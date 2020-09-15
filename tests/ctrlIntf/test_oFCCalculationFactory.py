# This file is part of ts_ofc.
#
# Developed for the LSST Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import unittest

from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationFactory import OFCCalculationFactory
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfLsst import OFCCalculationOfLsst
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfComCam import OFCCalculationOfComCam
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfSh import OFCCalculationOfSh
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfCmos import OFCCalculationOfCmos
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfLsstFam import OFCCalculationOfLsstFam


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

        calculator = OFCCalculationFactory.getCalculator(
            InstName.LSST, state0Dof=self.state0Dof
        )
        self.assertTrue(isinstance(calculator, OFCCalculationOfLsst))

    def testGetCalculatorOfComCam(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.COMCAM)
        self.assertTrue(isinstance(calculator, OFCCalculationOfComCam))

    def testGetCalculatorOfComCamDof(self):

        calculator = OFCCalculationFactory.getCalculator(
            InstName.COMCAM, state0Dof=self.state0Dof
        )
        self.assertTrue(isinstance(calculator, OFCCalculationOfComCam))

    def testGetCalculatorOfSh(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.SH)
        self.assertTrue(isinstance(calculator, OFCCalculationOfSh))

    def testGetCalculatorOfShDoF(self):

        calculator = OFCCalculationFactory.getCalculator(
            InstName.SH, state0Dof=self.state0Dof
        )
        self.assertTrue(isinstance(calculator, OFCCalculationOfSh))

    def testGetCalculatorOfCmos(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.CMOS)
        self.assertTrue(isinstance(calculator, OFCCalculationOfCmos))

    def testGetCalculatorOfCmosDoF(self):

        calculator = OFCCalculationFactory.getCalculator(
            InstName.CMOS, state0Dof=self.state0Dof
        )
        self.assertTrue(isinstance(calculator, OFCCalculationOfCmos))

    def testGetCalculatorOfLsstFam(self):

        calculator = OFCCalculationFactory.getCalculator(InstName.LSSTFAM)
        self.assertTrue(isinstance(calculator, OFCCalculationOfLsstFam))

    def testGetCalculatorOfLsstFamDof(self):

        calculator = OFCCalculationFactory.getCalculator(
            InstName.LSSTFAM, state0Dof=self.state0Dof
        )
        self.assertTrue(isinstance(calculator, OFCCalculationOfLsstFam))

    def testGetCalculatorOfWrongInst(self):

        self.assertRaises(ValueError, OFCCalculationFactory.getCalculator, "wrongInst")


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
