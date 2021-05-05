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

from lsst.ts.ofc.utils import get_pkg_root, get_config_dir, rot_1d_array
from lsst.ts.ofc import CamRot


class TestUtils(unittest.TestCase):
    """Test the OFCCalculation class."""

    def test_get_pkg_root(self):

        pkg_root = get_pkg_root()

        self.assertTrue(pkg_root.exists())

        init_file = pkg_root / "python" / "lsst" / "ts" / "ofc" / "__init__.py"

        self.assertTrue(init_file.exists(), f"File {init_file} does not exists.")

    def test_get_config_dir(self):

        config_dir = get_config_dir()

        self.assertTrue(config_dir.exists())

    def test_rot_1d_array(self):

        vec = np.array([1.0, 0.0])

        angle = 0.0
        rot_mat = CamRot.rot_mat(angle)
        rot_vec = rot_1d_array(vec, rot_mat)

        self.assertEqual(vec[0], rot_vec[0])
        self.assertEqual(vec[1], rot_vec[1])

        angle = 45.0
        rot_mat = CamRot.rot_mat(angle)
        rot_vec = rot_1d_array(vec, rot_mat)

        expected_value = np.sin(np.radians(angle))
        self.assertAlmostEqual(rot_vec[0], expected_value)
        self.assertAlmostEqual(rot_vec[1], expected_value)

        angle = 90.0
        rot_mat = CamRot.rot_mat(angle)
        rot_vec = rot_1d_array(vec, rot_mat)

        self.assertAlmostEqual(rot_vec[0], vec[1])
        self.assertAlmostEqual(rot_vec[1], vec[0])


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
