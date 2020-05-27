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

import numpy as np
import unittest

from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfIota import OFCCalculationOfIota


class TestOFCCalculationOfIota(unittest.TestCase):
    """Test the OFCCalculationOfIota class."""

    def setUp(self):

        self.ofcCalculation = OFCCalculationOfIota(InstName.COMCAM, "sh")

    def testZkAndDofIdxFromConfigFile(self):

        dataShare = self.ofcCalculation.ztaac.dataShare
        zn3Idx = dataShare.getZn3Idx()
        dofIdx = dataShare.getDofIdx()

        ansZn3Idx = np.arange(19)
        ansDofIdx = np.arange(10)

        deltaZn3 = np.sum(np.abs(zn3Idx - ansZn3Idx))
        deltaDof = np.sum(np.abs(dofIdx - ansDofIdx))

        self.assertEqual(deltaZn3, 0)
        self.assertEqual(deltaDof, 0)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
