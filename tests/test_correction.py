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

from lsst.ts.ofc import Correction
from lsst.ts.ofc.utils import CorrectionType


class TestCorrection(unittest.TestCase):
    """Test the Correction class."""

    def test_position_init_as_array(self) -> None:
        """Test the position correction initialization with an array."""
        values = np.random.rand(6)
        correction = Correction(values)

        self.assertEqual(correction.correction_type, CorrectionType.POSITION)
        self.assertTrue(np.all(correction() == values))

    def test_position_init_as_args(self) -> None:
        """Test the position correction initialization with args."""
        values = np.random.rand(6)
        correction = Correction(*values)

        self.assertEqual(correction.correction_type, CorrectionType.POSITION)
        self.assertTrue(np.all(correction() == values))

    def test_bend_72_init_as_array(self) -> None:
        """Test the bend 72 correction initialization with an array."""
        values = np.random.rand(72)
        correction = Correction(values)

        self.assertEqual(correction.correction_type, CorrectionType.FORCE)
        self.assertTrue(np.all(correction() == values))

    def test_bend_72_init_as_args(self) -> None:
        """Test the bend 72 correction initialization with args."""
        values = np.random.rand(72)
        correction = Correction(*values)

        self.assertEqual(correction.correction_type, CorrectionType.FORCE)
        self.assertTrue(np.all(correction() == values))

    def test_bend_156_init_as_array(self) -> None:
        """Test the bend 156 correction initialization with an array."""
        values = np.random.rand(156)
        correction = Correction(values)

        self.assertEqual(correction.correction_type, CorrectionType.FORCE)
        self.assertTrue(np.all(correction() == values))

    def test_bend_156_init_as_args(self) -> None:
        """Test the bend 156 correction initialization with args."""
        values = np.random.rand(156)
        correction = Correction(*values)

        self.assertEqual(correction.correction_type, CorrectionType.FORCE)
        self.assertTrue(np.all(correction() == values))

    def test_unknown_init_as_array(self) -> None:
        """Test the unknown correction initialization with an array."""
        n_values_1 = np.random.randint(low=1, high=6)
        n_values_2 = np.random.randint(low=7, high=72)
        n_values_3 = np.random.randint(low=73, high=156)
        n_values_4 = np.random.randint(low=157, high=300)

        for n_value in [n_values_1, n_values_2, n_values_3, n_values_4]:
            with self.subTest(n_value=n_value):
                values = np.random.rand(n_value)
                correction = Correction(values)

                self.assertEqual(correction.correction_type, CorrectionType.UNKNOWN)
                self.assertTrue(np.all(correction() == values))

    def test_unknown_init_as_args(self) -> None:
        """Test the unknown correction initialization with args."""
        n_values_1 = np.random.randint(low=1, high=6)
        n_values_2 = np.random.randint(low=7, high=72)
        n_values_3 = np.random.randint(low=73, high=156)
        n_values_4 = np.random.randint(low=157, high=300)

        for n_value in [n_values_1, n_values_2, n_values_3, n_values_4]:
            with self.subTest(n_value=n_value):
                values = np.random.rand(n_value)
                correction = Correction(*values)

                self.assertEqual(correction.correction_type, CorrectionType.UNKNOWN)
                self.assertTrue(np.all(correction() == values))


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
