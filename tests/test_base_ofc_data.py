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

        self.assertEqual(base_ofc_data.iqw_filename, "imgQualWgt.yaml")
        self.assertEqual(base_ofc_data.y2_filename, "y2.yaml")
        self.assertEqual(
            base_ofc_data.sensor_mapping_filename, "sensorNameToFieldIdx.yaml"
        )
        self.assertEqual(base_ofc_data.dof_state0_filename, "state0inDof.yaml")
        self.assertEqual(base_ofc_data.intrinsic_zk_filename_root, "intrinsicZn")
        self.assertEqual(base_ofc_data.sen_m_filename_root, "senM")

    def test_constructor_with_args(self):

        base_ofc_data = BaseOFCData(
            iqw_filename="new_imgQualWgt.yaml",
            y2_filename="new_y2.yaml",
            sensor_mapping_filename="new_sensorNameToFieldIdx.yaml",
            dof_state0_filename="new_state0inDof.yaml",
            intrinsic_zk_filename_root="new_intrinsicZn",
            sen_m_filename_root="new_senM",
        )

        self.assertEqual(base_ofc_data.iqw_filename, "new_imgQualWgt.yaml")
        self.assertEqual(base_ofc_data.y2_filename, "new_y2.yaml")
        self.assertEqual(
            base_ofc_data.sensor_mapping_filename, "new_sensorNameToFieldIdx.yaml"
        )
        self.assertEqual(base_ofc_data.dof_state0_filename, "new_state0inDof.yaml")
        self.assertEqual(base_ofc_data.intrinsic_zk_filename_root, "new_intrinsicZn")
        self.assertEqual(base_ofc_data.sen_m_filename_root, "new_senM")


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
