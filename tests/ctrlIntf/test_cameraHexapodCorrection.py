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

from lsst.ts.ofc.ctrlIntf.CameraHexapodCorrection import CameraHexapodCorrection


class TestCameraHexapodCorrection(unittest.TestCase):
    """Test the CameraHexapodCorrection class."""

    def setUp(self):

        self.x = 0.1
        self.y = 0.2
        self.z = 0.3
        self.u = 0.4
        self.v = 0.5
        self.w = 0.6
        self.hexapodCorrection = CameraHexapodCorrection(
            self.x, self.y, self.z, self.u, self.v, w=self.w
        )

    def testGetCorrection(self):

        x, y, z, u, v, w = self.hexapodCorrection.getCorrection()
        self.assertEqual(self.x, x)
        self.assertEqual(self.y, y)
        self.assertEqual(self.z, z)
        self.assertEqual(self.u, u)
        self.assertEqual(self.v, v)
        self.assertEqual(self.w, w)

    def testSetCorrection(self):

        x = 0.2
        y = 0.3
        z = 0.4
        u = 0.5
        v = 0.6
        w = 0.7
        self.hexapodCorrection.setCorrection(x, y, z, u, v, w=w)

        (
            xInHex,
            yInHex,
            zInHex,
            uInHex,
            vInHex,
            wInHex,
        ) = self.hexapodCorrection.getCorrection()
        self.assertEqual(xInHex, x)
        self.assertEqual(yInHex, y)
        self.assertEqual(zInHex, z)
        self.assertEqual(uInHex, u)
        self.assertEqual(vInHex, v)
        self.assertEqual(wInHex, w)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
