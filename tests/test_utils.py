# This file is part of ts_ofc
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

import unittest

import numpy as np
from lsst.ts.ofc import OFCData
from lsst.ts.ofc.utils import (
    get_config_dir,
    get_field_angles,
    get_pkg_root,
    rot_1d_array,
)
from lsst.ts.ofc.utils.intrinsic_zernikes import intrinsic_zernikes


class TestUtils(unittest.TestCase):
    """Test the OFCCalculation class."""

    def setUp(self):
        self.ofc_data = OFCData("lsst")

    def test_get_pkg_root(self):
        pkg_root = get_pkg_root()

        self.assertTrue(pkg_root.exists())

    def test_get_config_dir(self):
        config_dir = get_config_dir()

        self.assertTrue(config_dir.exists())

    def test_rot_1d_array(self):
        vec = np.array([1.0, 0.0])

        def compute_rot_mat(rot):
            """Return rotation matrix."""
            rot_rad = np.deg2rad(rot)
            c, s = np.cos(rot_rad), np.sin(rot_rad)
            return np.array(((c, -s), (s, c)))

        angle = 0.0
        rot_mat = compute_rot_mat(angle)
        rot_vec = rot_1d_array(vec, rot_mat)

        self.assertEqual(vec[0], rot_vec[0])
        self.assertEqual(vec[1], rot_vec[1])

        angle = 45.0
        rot_mat = compute_rot_mat(angle)
        rot_vec = rot_1d_array(vec, rot_mat)

        expected_value = np.sin(np.radians(angle))
        self.assertAlmostEqual(rot_vec[0], expected_value)
        self.assertAlmostEqual(rot_vec[1], expected_value)

        angle = 90.0
        rot_mat = compute_rot_mat(angle)
        rot_vec = rot_1d_array(vec, rot_mat)

        self.assertAlmostEqual(rot_vec[0], vec[1])
        self.assertAlmostEqual(rot_vec[1], vec[0])

    def test_get_field_angles(self):
        sensor_names = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]

        field_x, field_y = zip(*get_field_angles(sensor_names))

        self.assertEqual(len(field_x), len(sensor_names))
        self.assertEqual(len(field_y), len(sensor_names))

        sensor_field_angles = [
            [1.1902777777777778, -1.1902777777777778],
            [1.1902777777777778, 1.1902777777777778],
            [-1.1902777777777778, -1.1902777777777778],
            [-1.1902777777777778, 1.1902777777777778],
        ]

        for idx in range(len(field_x)):
            self.assertEqual(field_x[idx], sensor_field_angles[idx][0])
            self.assertEqual(field_y[idx], sensor_field_angles[idx][1])

        sensor_names = ["R03_S12"]
        print(get_field_angles(sensor_names))

    def test_get_intrinsic_zernikes(self):
        sensor_names = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]
        field_angles = get_field_angles(sensor_names)

        for filter_name in self.ofc_data.eff_wavelength:
            with self.subTest(filter_name=filter_name):
                intrinsic_zk = intrinsic_zernikes(
                    self.ofc_data, filter_name, field_angles
                )
                self.assertTrue(isinstance(intrinsic_zk, np.ndarray))
                self.assertEqual(len(intrinsic_zk), 4)

        with self.assertRaises(RuntimeError):
            intrinsic_zernikes(self.ofc_data, "bad_filter_name", field_angles)


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
