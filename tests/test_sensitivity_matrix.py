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

import pathlib
import unittest

import numpy as np

from lsst.ts.ofc import OFCData, StateEstimator, SensitivityMatrix


class TestSensitivityMatrix(unittest.TestCase):
    """Test the OptStateEsti class."""

    def setUp(self):
        self.ofc_data = OFCData("lsst")

        self.sensor_names = ["R44_SW0", "R04_SW0", "R00_SW0", "R40_SW0"]

    def test_sensitivity(self):
        sensitivity_matrix = SensitivityMatrix(0.0, self.sensor_names)

        print(sensitivity_matrix)
    

if __name__ == "__main__":
    # Run the unit test
    unittest.main()
