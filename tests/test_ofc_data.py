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

from lsst.ts.ofc import OFCData

STD_TIMEOUT = 30


class TestOFCData(unittest.TestCase):
    """Test the OFCData class when not using asyncio."""

    def test_comcam(self):

        ofc_data = OFCData("comcam")

        self.assertEqual(ofc_data.name, "comcam")

    def test_lsst(self):

        ofc_data = OFCData("lsst")
        self.assertEqual(ofc_data.name, "lsst")

    def test_lsstfam(self):

        ofc_data = OFCData("lsstfam")

        self.assertEqual(ofc_data.name, "lsstfam")


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
