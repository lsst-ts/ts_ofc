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

from lsst.ts.ofc.ofc_data import BaseOFCData


class TestBaseOFCData(unittest.TestCase):
    """Test the OFCData class when not using asyncio."""

    def test_constructor(self):
        base_ofc_data = BaseOFCData()

        self.assertEqual(base_ofc_data.y2_filename_root, "_y2.yaml")
        self.assertEqual(base_ofc_data.dof_state0_filename, "state0_in_dof.yaml")
        self.assertEqual(base_ofc_data.intrinsic_zk_filename_root, "intrinsic_zk")
        self.assertEqual(base_ofc_data.sen_m_filename_root, "sensitivity")

    def test_constructor_with_args(self):
        base_ofc_data = BaseOFCData(
            y2_filename_root="_new_y2.yaml",
            dof_state0_filename="new_state0_in_dof.yaml",
            intrinsic_zk_filename_root="new_intrinsic_zk",
            sen_m_filename_root="new_sensitivity",
        )

        self.assertEqual(base_ofc_data.y2_filename_root, "_new_y2.yaml")
        self.assertEqual(base_ofc_data.dof_state0_filename, "new_state0_in_dof.yaml")
        self.assertEqual(base_ofc_data.intrinsic_zk_filename_root, "new_intrinsic_zk")
        self.assertEqual(base_ofc_data.sen_m_filename_root, "new_sensitivity")


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
