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
from lsst.ts.ofc import CamRot


class TestCamRot(unittest.TestCase):
    """Test the CamRot class."""

    def setUp(self):
        self.cam_rot = CamRot()

    def test_rot_comp_dof_m2hex(self):
        self.cam_rot.rot = 45

        component = "m2HexPos"
        dof_state = [1, 2, 2, 4, 4]
        tilt_xy = (1224, 0)
        rot_dof_state = self.cam_rot.rot_comp_dof(component, dof_state, tilt_xy)

        self.assertAlmostEqual(rot_dof_state[1], 0.00841705, places=7)

    def test_rot_comp_dof_camhex(self):
        self.cam_rot.rot = 90
        component = "camHexPos"
        dof_state = [1, 2, 3, 4, 5]
        tilt_xy = (0, 0)
        rot_dof_state = self.cam_rot.rot_comp_dof(component, dof_state, tilt_xy)

        ans = [1, -3, 2, -5, 4]
        delta = np.sum(np.abs(rot_dof_state - ans))
        self.assertEqual(delta, 0)

    def test_rot_comp_dof_m1m3bend(self):
        self.cam_rot.rot = 45
        component = "M1M3Bend"

        num_bend_mode = 20
        dof_state = np.zeros(num_bend_mode)
        dof_state[0] = 1
        dof_state[2] = 2
        tilt_xy = (0, 0)

        rot_dof_state = self.cam_rot.rot_comp_dof(component, dof_state, tilt_xy)

        self.assertAlmostEqual(rot_dof_state[0], 0.70710678, places=7)
        self.assertEqual(rot_dof_state[2], 2)
        self.assertEqual(len(rot_dof_state), num_bend_mode)

    def test_rot_comp_dof_m2bend(self):
        self.cam_rot.rot = 45
        component = "M2Bend"

        num_bend_mode = 20
        dof_state = np.zeros(num_bend_mode)
        dof_state[0] = 1
        dof_state[4] = 2
        tilt_xy = (0, 0)

        rot_dof_state = self.cam_rot.rot_comp_dof(component, dof_state, tilt_xy)

        self.assertAlmostEqual(rot_dof_state[0], 0.70710678, places=7)
        self.assertEqual(rot_dof_state[4], 2)
        self.assertEqual(len(rot_dof_state), num_bend_mode)

    def test_bad_component_name(self):
        dof_state = np.zeros(20)

        with self.assertRaises(RuntimeError):
            self.cam_rot.rot_comp_dof("NoValidComp", dof_state)

        with self.assertRaises(RuntimeError):
            self.cam_rot.rot_comp_dof("BothHexPosBend", dof_state)


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
