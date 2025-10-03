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
from lsst.ts.ofc import OFCData

STD_TIMEOUT = 30


class TestOFCDataConstructor(unittest.TestCase):
    """Test the OFCData class when not using asyncio."""

    def test_comcam(self) -> None:
        """Test the OFCData class with the comcam instrument."""
        ofc_data = OFCData("comcam")

        self.assertEqual(ofc_data.name, "comcam")

    def test_lsst(self) -> None:
        """Test the OFCData class with the lsst instrument."""
        ofc_data = OFCData("lsst")
        self.assertEqual(ofc_data.name, "lsst")

    def test_lsstfam(self) -> None:
        """Test the OFCData class with the lsstfam instrument."""
        ofc_data = OFCData("lsstfam")

        self.assertEqual(ofc_data.name, "lsstfam")


class TestOFCData(unittest.TestCase):
    def setUp(self) -> None:
        """Set up the test case."""
        self.ofc_data = OFCData("lsst")
        file_path = (
            pathlib.Path(__file__).parent.absolute()
            / "testData"
            / "test_controller.yaml"
        )
        self.ofc_data.controller_filename = file_path

    def test_xref(self) -> None:
        """Test the xref property."""
        self.assertEqual(self.ofc_data.xref, "x00")

        for xref in self.ofc_data.xref_list:
            self.ofc_data.xref = xref
            self.assertEqual(self.ofc_data.xref, xref)

        with self.assertRaises(ValueError):
            self.ofc_data.xref = "bad_xref"

    def test_dof_idx(self) -> None:
        """Test the dof_idx property."""
        self.assertTrue(isinstance(self.ofc_data.dof_idx, np.ndarray))
        self.assertEqual(len(self.ofc_data.dof_idx), 50)

        with self.assertRaises(AttributeError):
            self.ofc_data.dof_idx = np.zeros_like(self.ofc_data.dof_idx)

    def test_change_controller_configuration(self) -> None:
        """Test changing the controller configuration."""
        ofc_data = OFCData("lsst")
        initial_kd = ofc_data.controller["kd"]

        ofc_data.controller_filename = "pid_controller.yaml"

        self.assertNotEqual(ofc_data.controller["kd"], initial_kd)

    def test_selected_zn_idx(self) -> None:
        """Test the selected_zn_idx property."""
        self.assertTrue(isinstance(self.ofc_data.zn_selected, np.ndarray))

        # Check ability to set the selected_zn_idx
        new_zn_selected = np.array([4, 5, 10, 20, 25])
        self.ofc_data.zn_selected = new_zn_selected
        self.assertEqual(len(self.ofc_data.zn_idx), 5)
        np.testing.assert_array_equal(
            self.ofc_data.zn_idx, new_zn_selected - self.ofc_data.znmin
        )

        # Check that selecting zernikes below znmin limit raises an error
        with self.assertRaises(ValueError):
            self.ofc_data.zn_selected = [1, 2, 3]

        # Check that selecting zernikes above znmax limit raises an error
        with self.assertRaises(ValueError):
            self.ofc_data.zn_selected = [29, 30]

    def test_comp_dof_idx(self) -> None:
        """Test the comp_dof_idx property."""
        self.assertTrue(isinstance(self.ofc_data.comp_dof_idx, dict))

        for comp in {"m2HexPos", "camHexPos", "M1M3Bend", "M2Bend"}:
            with self.subTest(comp=comp):
                self.assertTrue(comp in self.ofc_data.comp_dof_idx)

            for item in {"startIdx", "idxLength", "state0name", "rot_mat"}:
                with self.subTest(comp=comp, item=item):
                    self.assertTrue(item in self.ofc_data.comp_dof_idx[comp])

        new_dof_mask = dict(
            m2HexPos=np.zeros(5, dtype=bool),
            camHexPos=np.ones(5, dtype=bool),
            M1M3Bend=np.zeros(20, dtype=bool),
            M2Bend=np.zeros(20, dtype=bool),
        )

        self.ofc_data.comp_dof_idx = new_dof_mask

        self.assertEqual(len(self.ofc_data.dof_idx), 5)

        with self.assertRaises(ValueError):
            self.ofc_data.comp_dof_idx = np.zeros_like(self.ofc_data.dof_idx)

        # m2HexPos has the wrong number of elements; 4 instead of 5
        new_dof_mask = dict(
            m2HexPos=np.zeros(4, dtype=bool),
            camHexPos=np.ones(5, dtype=bool),
            M1M3Bend=np.zeros(20, dtype=bool),
            M2Bend=np.zeros(20, dtype=bool),
        )

        with self.assertRaises(RuntimeError):
            self.ofc_data.comp_dof_idx = new_dof_mask


class TestAsyncOFCDataConstructor(unittest.IsolatedAsyncioTestCase):
    """Test the OFCData class when not using asyncio."""

    async def test_comcam(self) -> None:
        """Test the OFCData class with the comcam instrument."""
        ofc_data = OFCData()

        with self.assertRaises(RuntimeError):
            ofc_data.name

        await ofc_data.configure_instrument("comcam")

        self.assertEqual(ofc_data.name, "comcam")

    async def test_lsst(self) -> None:
        """Test the OFCData class with the lsst instrument."""
        ofc_data = OFCData()

        with self.assertRaises(RuntimeError):
            ofc_data.name

        await ofc_data.configure_instrument("lsst")

        self.assertEqual(ofc_data.name, "lsst")

    async def test_lsstfam(self) -> None:
        """Test the OFCData class with the lsstfam instrument."""
        ofc_data = OFCData()

        with self.assertRaises(RuntimeError):
            ofc_data.name

        await ofc_data.configure_instrument("lsstfam")

        self.assertEqual(ofc_data.name, "lsstfam")


if __name__ == "__main__":
    # Run the unit test
    unittest.main()
