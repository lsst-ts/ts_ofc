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

    def test_constructor(self) -> None:
        """Test the OFCData class with the lsst instrument."""
        base_ofc_data = BaseOFCData()

        self.assertEqual(base_ofc_data.y2_filename_root, "_y2.yaml")
        self.assertEqual(base_ofc_data.dof_state0_filename, "state0_in_dof.yaml")
        self.assertEqual(base_ofc_data.intrinsic_zk_filename_root, "intrinsic_zk")
        self.assertEqual(base_ofc_data.sen_m_filename_root, "sensitivity")
        self.assertEqual(base_ofc_data.m1m3_force_range, 67 * 2)
        self.assertEqual(base_ofc_data.m2_force_range, 22.5 * 2)
        self.assertEqual(base_ofc_data.dof_indices["M2_hexapod"][0], 0)
        self.assertEqual(base_ofc_data.dof_indices["M2_hexapod"][1], 5)
        self.assertEqual(base_ofc_data.dof_indices["CAM_hexapod"][0], 5)
        self.assertEqual(base_ofc_data.dof_indices["CAM_hexapod"][1], 10)
        self.assertEqual(base_ofc_data.dof_indices["M1M3_bending"][0], 10)
        self.assertEqual(base_ofc_data.dof_indices["M1M3_bending"][1], 30)
        self.assertEqual(base_ofc_data.dof_indices["M2_bending"][0], 30)
        self.assertEqual(base_ofc_data.dof_indices["M2_bending"][1], 50)

    def test_constructor_with_args(self) -> None:
        """Test the OFCData class with the lsst instrument."""
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
