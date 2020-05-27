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

from lsst.ts.ofc.SubSysAdap import SubSysAdap
from lsst.ts.ofc.Utility import DofGroup, getConfigDir


class TestSubSysAdap(unittest.TestCase):
    """Test the SubSysAdap class."""

    def setUp(self):

        self.configDir = getConfigDir()

        self.subSysAdap = SubSysAdap()
        self.subSysAdap.config(self.configDir)

    def testConfig(self):

        self._testRotMatShape(self.subSysAdap, DofGroup.M2HexPos, (5, 6))
        self._testRotMatShape(self.subSysAdap, DofGroup.CamHexPos, (5, 6))

    def _testRotMatShape(self, subSysAdap, dofGroup, ansShape):

        rotMat = subSysAdap.getRotMatHexInDof(dofGroup)
        self.assertEqual(rotMat.shape, ansShape)

    def testGetRotMatHexInDof(self):

        subSysAdap = SubSysAdap()

        self._testRotMatShape(subSysAdap, DofGroup.M2HexPos, (0,))
        self._testRotMatShape(subSysAdap, DofGroup.CamHexPos, (0,))

        self.assertRaises(
            ValueError, self.subSysAdap.getRotMatHexInDof, DofGroup.M1M3Bend
        )
        self.assertRaises(
            ValueError, self.subSysAdap.getRotMatHexInDof, DofGroup.M2Bend
        )

    def testTransActForceToZemaxWithWrongInputDofGroup(self):

        self.assertRaises(
            ValueError,
            self.subSysAdap.transActForceToSubSys,
            DofGroup.M2HexPos,
            np.array([0]),
        )

    def testTransActForceToZemax(self):

        actForce = np.ones(72)
        transActForce = self.subSysAdap.transActForceToZemax(DofGroup.M2Bend, actForce)

        ansActForce = -actForce
        delta = np.sum(np.abs(transActForce - ansActForce))
        self.assertEqual(delta, 0)

    def testTransActForceToSubSys(self):

        actForce = np.ones(72)
        transActForce = self.subSysAdap.transActForceToSubSys(DofGroup.M2Bend, actForce)

        ansActForce = -actForce
        delta = np.sum(np.abs(transActForce - ansActForce))
        self.assertEqual(delta, 0)

    def testTransHexaPosToZemax(self):

        hexaPos = np.array([1, 2, 3, 1, 1, 1])
        transHexPos = self.subSysAdap.transHexaPosToZemax(hexaPos)

        ansHexPos = [-3, -1, 2, -3600, 3600]
        self.assertEqual(transHexPos.tolist(), ansHexPos)

    def testTransHexaPosToSubSys(self):

        hexaPos = np.array([1, 2, 3, 3600, 3600])
        transHexPos = self.subSysAdap.transHexaPosToSubSys(hexaPos)

        ansHexPos = [-2, 3, -1, -1, 1, 0]
        self.assertEqual(transHexPos.tolist(), ansHexPos)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
