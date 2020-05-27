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
import numpy as np

from lsst.ts.ofc.ctrlIntf.M2Correction import M2Correction


class TestM2Correction(unittest.TestCase):
    """Test the M2Correction class."""

    def setUp(self):

        self.zForces = np.arange(M2Correction.NUM_OF_ACT)
        self.m2Correction = M2Correction(self.zForces)

    def testGetZForces(self):

        zForces = self.m2Correction.getZForces()
        self.assertTrue(isinstance(zForces, np.ndarray))

        delta = np.sum(np.abs(zForces - self.zForces))
        self.assertEqual(delta, 0)

    def testSetZForces(self):

        zForces = np.arange(M2Correction.NUM_OF_ACT) * 10
        self.m2Correction.setZForces(zForces)

        zForcesInM1M3 = self.m2Correction.getZForces()
        delta = np.sum(np.abs(zForcesInM1M3 - zForces))
        self.assertEqual(delta, 0)

    def testSetZForcesWithWrongLength(self):

        zForces = np.arange(M2Correction.NUM_OF_ACT + 1)
        self.assertRaises(ValueError, self.m2Correction.setZForces, zForces)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
