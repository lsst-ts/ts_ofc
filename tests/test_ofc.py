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

import numpy as np
import unittest

from lsst.ts.ofc import OFC, OFCData, Correction
from lsst.ts.ofc.utils import get_pkg_root, CorrectionType


class TestOFC(unittest.TestCase):
    """Test the OFCCalculation class."""

    def setUp(self):

        self.ofc_data = OFCData("lsst")
        self.ofc = OFC(self.ofc_data)
        self.test_data_path = (
            get_pkg_root() / "tests" / "testData" / "lsst_wfs_error_iter0.z4c"
        )

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
        filter_name = ""
        rot = 0.0

        wfe, field_idx = self._get_wfe()

        (
            m2_hex_corr,
            cam_hex_corr,
            m1m3_corr,
            m2_corr,
        ) = self.ofc.calculate_corrections(
            wfe=wfe, field_idx=field_idx, filter_name=filter_name, gain=gain, rot=rot
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

        # Data taken from previous version of the software.
        expected_m2_hex_corr = (
            2.5379271481981194,
            -0.5385152037171632,
            9.448475412170623,
            6.371036372249689e-05,
            -0.00011220461454586595,
            0.0,
        )
        expected_cam_hex_corr = (
            -1.1955042327995036,
            3.2532120407166447,
            39.918997395310775,
            0.0004669118574001339,
            2.157033634143978e-05,
            0.0,
        )
        expected_m1m3_corr_sample = (
            6.40274808e00,
            2.71962001e00,
            2.37669494e-01,
            -9.38012046e-01,
        )
        expected_m2_corr_sample = (
            0.16922937,
            -0.03938491,
            -0.35643931,
            -0.51508621,
            -0.38215294,
            -0.03123699,
        )

        for computed_value, expected_value in zip(m2_hex_corr(), expected_m2_hex_corr):
            with self.subTest(
                correction="M2Hexapod",
                computed_value=computed_value,
                expected_value=expected_value,
            ):
                self.assertAlmostEqual(computed_value, expected_value, places=7)

        for computed_value, expected_value in zip(
            cam_hex_corr(), expected_cam_hex_corr
        ):
            with self.subTest(
                correction="CamHexapod",
                computed_value=computed_value,
                expected_value=expected_value,
            ):
                self.assertAlmostEqual(computed_value, expected_value, places=7)

        for computed_value, expected_value in zip(
            m1m3_corr()[: len(expected_m1m3_corr_sample)], expected_m1m3_corr_sample
        ):
            with self.subTest(
                correction="M1M3",
                computed_value=computed_value,
                expected_value=expected_value,
            ):
                self.assertAlmostEqual(computed_value, expected_value, places=7)

        for computed_value, expected_value in zip(
            m2_corr()[: len(expected_m2_corr_sample)], expected_m2_corr_sample
        ):
            with self.subTest(
                correction="M2",
                computed_value=computed_value,
                expected_value=expected_value,
            ):
                self.assertAlmostEqual(computed_value, expected_value, places=7)

        self.assertAlmostEqual(self.ofc.lv_dof[0], -9.44847541, places=7)
        self.assertAlmostEqual(self.ofc.lv_dof[1], -2.53792714, places=7)
        self.assertAlmostEqual(self.ofc.lv_dof[5], -39.91899739, places=7)
        self.assertAlmostEqual(self.ofc.lv_dof[7], 3.25321204, places=7)

    def _get_wfe(self):

        wfe = np.loadtxt(self.test_data_path)

        sensor_name_list = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]

        field_idx = [
            self.ofc.ofc_data.field_idx[sensor_name] for sensor_name in sensor_name_list
        ]

        return wfe, field_idx

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
                wfe = self.ofc.ofc_data.get_intrinsic_zk(filter_name)
                field_idx = np.arange(wfe.shape[0])
                (
                    m2_hex_corr,
                    cam_hex_corr,
                    m1m3_corr,
                    m2_corr,
                ) = self.ofc.calculate_corrections(
                    wfe=wfe,
                    field_idx=field_idx,
                    filter_name=filter_name,
                    gain=1.0,
                    rot=0.0,
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
        new_comp_dof_idx = dict(
            m2HexPos=np.zeros(5, dtype=bool),
            camHexPos=np.ones(5, dtype=bool),
            M1M3Bend=np.zeros(20, dtype=bool),
            M2Bend=np.zeros(20, dtype=bool),
        )

        self.ofc.ofc_data.comp_dof_idx = new_comp_dof_idx

        self.assertEqual(len(self.ofc.ofc_data.dof_idx), 5)

        filter_name = ""

        wfe = self.ofc.ofc_data.get_intrinsic_zk(filter_name)

        wfe[:, 0:1] += 0.1  # add 0.1 um of defocus

        field_idx = np.arange(wfe.shape[0])
        (
            m2_hex_corr,
            cam_hex_corr,
            m1m3_corr,
            m2_corr,
        ) = self.ofc.calculate_corrections(
            wfe=wfe,
            field_idx=field_idx,
            filter_name=filter_name,
            gain=1.0,
            rot=0.0,
        )

        x, y, z, u, v, w = cam_hex_corr()

        self.assertAlmostEqual(x, 0.00011914744971686098)
        self.assertAlmostEqual(y, -5.2710512039956525e-05)
        self.assertAlmostEqual(z, -6.271489529009416)
        self.assertAlmostEqual(u, 0.0)
        self.assertAlmostEqual(v, 0.0)
        self.assertAlmostEqual(w, 0.0)

        self.assertTrue(np.allclose(m2_hex_corr(), np.zeros_like(m2_hex_corr())))
        self.assertTrue(np.allclose(m1m3_corr(), np.zeros_like(m1m3_corr())))
        self.assertTrue(np.allclose(m2_corr(), np.zeros_like(m2_corr())))


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
