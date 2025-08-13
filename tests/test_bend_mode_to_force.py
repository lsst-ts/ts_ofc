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
from lsst.ts.ofc import BendModeToForce, OFCData


class TestBendModeToForce(unittest.TestCase):
    """Test the BendModeToForce class."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.ofc_data = OFCData("comcam")
        self.bmf_m1m3 = BendModeToForce(component="M1M3", ofc_data=self.ofc_data)
        self.bmf_m2 = BendModeToForce(component="M2", ofc_data=self.ofc_data)

    def test_init(self) -> None:
        """Test class initialization."""
        self.assertEqual(self.bmf_m1m3.rot_mat.shape, (156, 20))
        self.assertEqual(self.bmf_m1m3.rot_mat[0, 0], 0.07088527)
        self.assertEqual(self.bmf_m1m3.rot_mat[0, 1], -0.9108789)
        self.assertEqual(self.bmf_m1m3.rot_mat[1, 0], 0.192324)
        self.assertEqual(self.bmf_m1m3.rot_mat[1, 1], -2.764459)
        self.assertEqual(self.bmf_m1m3.bending_mode_stresses_positive.shape, (20,))
        self.assertEqual(self.bmf_m1m3.bending_mode_stresses_negative.shape, (20,))

        # Computed using previous version of the code.
        self.assertEqual(self.bmf_m2.rot_mat.shape, (72, 20))
        self.assertEqual(self.bmf_m2.rot_mat[0, 0], 2.2668080189579998)
        self.assertEqual(self.bmf_m2.rot_mat[0, 1], -0.507467616726)
        self.assertEqual(self.bmf_m2.rot_mat[1, 0], 2.282749549794)
        self.assertEqual(self.bmf_m2.rot_mat[1, 1], 0.462890224818)
        self.assertEqual(self.bmf_m2.bending_mode_stresses_positive.shape, (20,))
        self.assertEqual(self.bmf_m2.bending_mode_stresses_negative.shape, (20,))

    def test_m1m3_bending_mode_stresses(self) -> None:
        """Test the bending mode to stress per bending mode calculation."""
        dof = np.zeros(20)
        dof[0] = 1
        stresses = self.bmf_m1m3.get_stresses_from_dof(dof)

        expected_stresses = np.zeros(20)
        expected_stresses[0] = self.bmf_m1m3.bending_mode_stresses_positive[0]

        np.testing.assert_allclose(stresses, expected_stresses)

    def test_m1m3_force(self) -> None:
        """Test the force calculation for M1M3."""
        dof = np.zeros(20)
        dof[0:3] = np.array([1, 2, 3])
        force = self.bmf_m1m3.force(dof)

        self.assertEqual(len(force), 156)
        self.assertAlmostEqual(force[0], 222.57988747, places=7)

    def test_m2_force(self) -> None:
        """Test the force calculation for M2."""
        dof = np.zeros(20)
        dof[0:3] = np.array([1, 2, 3])
        force = self.bmf_m2.force(dof)

        self.assertEqual(len(force), 72)
        self.assertAlmostEqual(force[0], 1.2460073, places=7)

    def test_m1m3_bending_mode(self) -> None:
        """Test the bending mode calculation for M1M3."""
        dof = np.zeros(20)
        dof[0:3] = np.array([1, 2, 3])
        force = self.bmf_m1m3.force(dof)

        bm = self.bmf_m1m3.bending_mode(force)

        delta = np.sum(np.abs(bm - dof))
        self.assertLess(delta, 1e-10)

    def test_bad_init(self) -> None:
        """Test the class initialization with a bad component name."""
        with self.assertRaises(RuntimeError):
            BendModeToForce(component="camHex", ofc_data=self.ofc_data)


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
