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
from lsst.ts.ofc import OFC, Correction, OFCData
from lsst.ts.ofc.utils import CorrectionType, get_field_angles
from lsst.ts.ofc.utils.intrinsic_zernikes import intrinsic_zernikes


class TestOFC(unittest.TestCase):
    """Test the OFCCalculation class."""

    def setUp(self):
        self.ofc_data = OFCData("lsst")
        self.ofc_data.motion_penalty = (
            0.0001  # Set small motion penalty to allow for larger corrections
        )
        self.ofc = OFC(self.ofc_data)
        self.test_data_path = (
            pathlib.Path(__file__).parent.absolute()
            / "testData"
            / "lsst_wfs_error_test_ofc.z4c"
        )

        self.wfe = np.loadtxt(self.test_data_path)
        self.sensor_name_list = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]
        self.field_angles = get_field_angles(self.sensor_name_list)

    def test_init_lv_dof(self):
        self.ofc.lv_dof = np.random.rand(len(self.ofc.ofc_controller.dof_state0))

        self.ofc.init_lv_dof()

        self.assertTrue(np.all(self.ofc.lv_dof == 0))

    def test_pssn_data(self):
        self.assertTrue("sensor_id" in self.ofc.pssn_data)
        self.assertTrue("pssn" in self.ofc.pssn_data)
        self.assertTrue(self.ofc.pssn_data["sensor_id"] is None)
        self.assertTrue(self.ofc.pssn_data["pssn"] is None)

    def test_set_fwhm_data(self):
        fwhm_values = np.ones((5, 19)) * 0.2
        sensor_id = np.arange(5)

        self.ofc.set_fwhm_data(fwhm_values, sensor_id)

        self.assertTrue(np.all(sensor_id == self.ofc.pssn_data["sensor_id"]))
        self.assertAlmostEqual(self.ofc.pssn_data["pssn"][0], 0.9139012, places=6)

    def test_set_fwhm_data_fails(self):
        # Passing fwhm_values with 4 columns instead of 5
        fwhm_values = np.ones((4, 19)) * 0.2
        sensor_id = np.arange(5)

        with self.assertRaises(RuntimeError):
            self.ofc.set_fwhm_data(fwhm_values, sensor_id)

    def test_reset(self):
        dof = np.ones_like(self.ofc.ofc_controller.dof_state)
        self.ofc.ofc_controller.aggregate_state(dof, self.ofc.ofc_data.dof_idx)
        self.ofc.set_last_visit_dof(dof)

        (
            m2HexapodCorrection,
            hexapodCorrection,
            m1m3Correction,
            m2Correction,
        ) = self.ofc.reset()

        self.assertTrue(isinstance(m2HexapodCorrection, Correction))
        self.assertTrue(isinstance(hexapodCorrection, Correction))
        self.assertTrue(isinstance(m1m3Correction, Correction))
        self.assertTrue(isinstance(m2Correction, Correction))

        self.assertEqual(np.sum(m2HexapodCorrection()), 0)
        self.assertEqual(np.sum(hexapodCorrection()), 0)
        self.assertEqual(np.sum(m1m3Correction()), 0)
        self.assertEqual(np.sum(m2Correction()), 0)

        self.assertEqual(len(self.ofc.lv_dof), 50)
        self.assertEqual(np.sum(np.abs(self.ofc.lv_dof)), 0)

    def test_set_pssn_gain_unconfigured(self):
        with self.assertRaises(RuntimeError):
            self.ofc.set_pssn_gain()

    def test_set_pssn_gain(self):
        fwhm_values = np.ones((5, 19)) * 0.2
        sensor_id = np.arange(5)

        self.ofc.set_fwhm_data(fwhm_values, sensor_id)

        self.ofc.set_pssn_gain()

        self.assertTrue(self.ofc.ofc_controller.gain, self.ofc.default_gain)

        fwhm_values = np.ones((5, 19))

        self.ofc.set_fwhm_data(fwhm_values, sensor_id)

        self.ofc.set_pssn_gain()

        self.assertTrue(self.ofc.ofc_controller.gain, 1.0)

    def test_calculate_corrections(self):
        gain = 1.0
        filter_name = "R"
        rotation_angle = 0.0

        self.ofc.ofc_data.xref = "0"

        self.ofc.ofc_controller.dof_state0[45] = 0.1
        self.ofc.ofc_controller.reset_dof_state()

        (
            m2_hex_corr,
            cam_hex_corr,
            m1m3_corr,
            m2_corr,
        ) = self.ofc.calculate_corrections(
            wfe=self.wfe,
            sensor_names=self.sensor_name_list,
            filter_name=filter_name,
            gain=gain,
            rotation_angle=rotation_angle,
        )

        self.assertTrue(isinstance(m2_hex_corr, Correction))
        self.assertTrue(isinstance(cam_hex_corr, Correction))
        self.assertTrue(isinstance(m1m3_corr, Correction))
        self.assertTrue(isinstance(m2_corr, Correction))

        self.assertEqual(m2_hex_corr.correction_type, CorrectionType.POSITION)
        self.assertEqual(cam_hex_corr.correction_type, CorrectionType.POSITION)
        self.assertEqual(m1m3_corr.correction_type, CorrectionType.FORCE)
        self.assertEqual(m2_corr.correction_type, CorrectionType.FORCE)

        self.assertEqual(len(m2_hex_corr()), 6)
        self.assertEqual(len(cam_hex_corr()), 6)
        self.assertEqual(len(m1m3_corr()), 156)
        self.assertEqual(len(m2_corr()), 72)

        for computed_value in m2_hex_corr():
            with self.subTest(correction="M2Hexapod", computed_value=computed_value):
                self.assertAlmostEqual(computed_value, 0.0, places=2)

        for computed_value in cam_hex_corr():
            with self.subTest(correction="CamHexapod", computed_value=computed_value):
                self.assertAlmostEqual(computed_value, 0.0, places=2)

        # Check corrections match the original DOF state up to 0.1ums
        for idx, computed_value, expected_value in zip(
            np.arange(50), self.ofc.lv_dof, self.ofc.ofc_controller.dof_state0
        ):
            with self.subTest(
                correction=f"Correction DOF {idx}",
                computed_value=computed_value,
                expected_value=expected_value,
            ):
                assert np.abs(expected_value + computed_value) < 1e-1

    def test_get_state_correction_from_last_visit(self):
        new_comp_dof_idx = dict(
            m2HexPos=np.zeros(5, dtype=bool),
            camHexPos=np.ones(5, dtype=bool),
            M1M3Bend=np.zeros(20, dtype=bool),
            M2Bend=np.zeros(20, dtype=bool),
        )

        self.ofc.ofc_data.comp_dof_idx = new_comp_dof_idx

        calc_dof = np.arange(1, 6)
        self.ofc.set_last_visit_dof(calc_dof)

        rearanged_dof = np.zeros(50)
        rearanged_dof[5:10] = calc_dof

        state_correction = self.ofc.lv_dof

        self.assertTrue(isinstance(self.ofc.lv_dof, np.ndarray))
        self.assertEqual(len(self.ofc.lv_dof), len(self.ofc.ofc_controller.dof_state0))

        delta = np.sum(np.abs(state_correction - rearanged_dof))
        self.assertEqual(delta, 0)

    def test_intrinsic_corr_is_zero(self):
        """Check that if we send intrinsic correction to the ofc we get zero
        for all corrections.
        """

        for filter_name in self.ofc.ofc_data.intrinsic_zk:
            with self.subTest(filter_name=filter_name):
                wfe = intrinsic_zernikes(self.ofc_data, filter_name, self.field_angles)

                (
                    m2_hex_corr,
                    cam_hex_corr,
                    m1m3_corr,
                    m2_corr,
                ) = self.ofc.calculate_corrections(
                    wfe=wfe,
                    sensor_names=self.sensor_name_list,
                    filter_name=filter_name,
                    gain=1.0,
                    rotation_angle=0.0,
                )
                self.assertTrue(
                    np.allclose(m2_hex_corr(), np.zeros_like(m2_hex_corr()))
                )
                self.assertTrue(
                    np.allclose(cam_hex_corr(), np.zeros_like(cam_hex_corr()))
                )
                self.assertTrue(np.allclose(m1m3_corr(), np.zeros_like(m1m3_corr())))
                self.assertTrue(np.allclose(m2_corr(), np.zeros_like(m2_corr())))

    def test_truncate_dof(self):
        """Check that we can truncate the number of degrees of freedom used
        in the calculation successfully.
        """

        # Set used degrees of freedom
        new_comp_dof_idx = dict(
            m2HexPos=np.zeros(5, dtype=bool),
            camHexPos=np.ones(5, dtype=bool),
            M1M3Bend=np.zeros(20, dtype=bool),
            M2Bend=np.zeros(20, dtype=bool),
        )
        self.ofc.ofc_data.comp_dof_idx = new_comp_dof_idx

        # Check that the number of degrees of freedom used is 5
        self.assertEqual(len(self.ofc.ofc_data.dof_idx), 5)

        # Set filter name, wavefront error
        filter_name = "R"

        wfe = intrinsic_zernikes(self.ofc_data, filter_name, self.field_angles)
        wfe[:, 0:1] += 0.1  # add 0.1 um of defocus

        # Calculate corrections
        (
            m2_hex_corr,
            cam_hex_corr,
            m1m3_corr,
            m2_corr,
        ) = self.ofc.calculate_corrections(
            wfe=wfe,
            sensor_names=self.sensor_name_list,
            filter_name=filter_name,
            gain=1.0,
            rotation_angle=0.0,
        )

        # Retrieve camera hexapod corrections
        x, y, z, u, v, w = cam_hex_corr()

        # Check that the camera hexapod corrections are right.
        # All of them should be zero except for defocus.
        self.assertAlmostEqual(x, 0.0, places=5)
        self.assertAlmostEqual(y, 0.0, places=5)
        self.assertAlmostEqual(z, -6, places=0)
        self.assertAlmostEqual(u, 0.0, places=9)
        self.assertAlmostEqual(v, 0.0, places=9)
        self.assertAlmostEqual(w, 0.0, places=9)

        # Check that the other corrections are zero
        self.assertTrue(np.allclose(m2_hex_corr(), np.zeros_like(m2_hex_corr())))
        self.assertTrue(np.allclose(m1m3_corr(), np.zeros_like(m1m3_corr())))
        self.assertTrue(np.allclose(m2_corr(), np.zeros_like(m2_corr())))

    def test_get_correction(self):
        # First time of calculation
        correction0 = self._calculate_cam_hex_correction()

        # Second time of calculation
        # The DOF should be aggregated
        correction = self._calculate_cam_hex_correction()

        # Check that the accumulated correction is
        # twice the original correction.
        # Note that this works because we reset the state both times
        self.assertAlmostEqual(correction[0], 2 * correction0[0])
        self.assertAlmostEqual(correction[1], 2 * correction0[1])
        self.assertAlmostEqual(correction[2], 2 * correction0[2])
        self.assertAlmostEqual(correction[3], 2 * correction0[3])
        self.assertAlmostEqual(correction[4], 2 * correction0[4])
        self.assertAlmostEqual(correction[5], 2 * correction0[5])

    def _calculate_cam_hex_correction(self):
        gain = 1.0
        filter_name = "R"
        rotation_angle = 0.0

        self.ofc.ofc_data.xref = "x0"

        # Set wavefront error
        wfe = intrinsic_zernikes(self.ofc_data, filter_name, self.field_angles)
        wfe[:, 0:1] += 0.1  # add 0.1 um of defocus

        # Calculate corrections
        self.ofc.calculate_corrections(
            wfe=wfe,
            sensor_names=self.sensor_name_list,
            filter_name=filter_name,
            gain=gain,
            rotation_angle=rotation_angle,
        )

        # Return corrections for camera hexapod.
        # Corrections are accumulated the second time this function is run.
        cam_hex_corr = self.ofc.get_correction("camHexPos")
        return cam_hex_corr.correction


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
