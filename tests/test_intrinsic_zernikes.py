# This file is part of ts_ofc.
#
# Developed for Vera Rubin Observatory.
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
from lsst.ts.ofc import OFCData


class TestIntrinsicZernikes(unittest.TestCase):
    def setUp(self):
        self.ofc_data = OFCData("lsst")

    def test_get_intrinsic_zk(self):
        for filter_name in self.ofc_data.eff_wavelength:
            with self.subTest(filter_name=filter_name):
                intrinsic_zk = self.ofc_data.get_intrinsic_zk(
                    filter_name, self.ofc_data.gq_points
                )
                self.assertTrue(isinstance(intrinsic_zk, np.ndarray))
                self.assertEqual(len(intrinsic_zk), 30)

                intrinsic_zk = self.ofc_data.get_intrinsic_zk(
                    filter_name, np.arange(3, 5)
                )
                self.assertEqual(len(intrinsic_zk), 2)

        with self.assertRaises(RuntimeError):
            self.ofc_data.get_intrinsic_zk("bad_filter_name")


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
