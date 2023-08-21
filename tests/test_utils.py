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


class TestUtils(unittest.TestCase):
    """Test the OFCCalculation class."""

    def test_get_pkg_root(self):
        pkg_root = get_pkg_root()

        self.assertTrue(pkg_root.exists())

    def test_get_config_dir(self):
        config_dir = get_config_dir()

        self.assertTrue(config_dir.exists())


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
