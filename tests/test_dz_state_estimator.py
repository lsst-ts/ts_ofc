# This file is part of ts_ofc.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import unittest

import numpy as np

from lsst.ts.ofc import DOF_UNITS_50, LABELS_50DOF, DoubleZernikeStateEstimator, OFCData

# The measured-intrinsic wavefront build's configuration: pupil Noll 4-26 less
# the two omitted terms, focal DZ orders 1-6, 50 DOF, 34 v-modes retained.
I_ZS = [j for j in range(4, 27) if j not in (20, 21)]
K_MIN = 1
K_MAX = 6
N_KEEP = 34
N_DOF = 50


class TestDoubleZernikeStateEstimator(unittest.TestCase):
    """Test the DoubleZernikeStateEstimator class."""

    def setUp(self) -> None:
        self.ofc_data = OFCData("lsst")
        self.estimator = DoubleZernikeStateEstimator(self.ofc_data, I_ZS, K_MIN, K_MAX, N_KEEP, n_dof=N_DOF)
        self.rng = np.random.default_rng(42)

    def test_shapes(self) -> None:
        """The decomposition has the shape the (k, j) grid implies."""
        n_kj = (K_MAX - K_MIN + 1) * len(I_ZS)
        self.assertEqual(len(self.estimator.kj_grid), n_kj)
        self.assertEqual(self.estimator.U_eff.shape, (n_kj, N_KEEP))
        self.assertEqual(self.estimator.V.shape, (N_DOF, N_DOF))
        self.assertEqual(self.estimator.n_keep_eff, N_KEEP)
        self.assertEqual(self.estimator.n_dof, N_DOF)

    def test_kj_grid_order(self) -> None:
        """The grid runs over k slowest and j fastest."""
        self.assertEqual(self.estimator.kj_grid[0], (K_MIN, I_ZS[0]))
        self.assertEqual(self.estimator.kj_grid[1], (K_MIN, I_ZS[1]))
        self.assertEqual(self.estimator.kj_grid[len(I_ZS)], (K_MIN + 1, I_ZS[0]))
        self.assertEqual(self.estimator.kj_grid[-1], (K_MAX, I_ZS[-1]))

    def test_pupil_axis_is_indexed_by_noll(self) -> None:
        """Pupil column j is Noll j, with no znmin offset.

        Both axes of the sensitivity matrix are 1-based index spaces with entry
        0 unused, so a Noll index is used as a column index directly. Getting
        this wrong is silent -- offsetting by znmin still yields a well-formed
        decomposition, of the wrong terms -- so it is asserted from the matrix
        rather than assumed.

        The evidence: index 0 is identically zero on both axes, and a
        rigid-body piston puts its response at low k and low j, where a znmin
        offset would place it in the middle of the retained pupil range.
        """
        sensitivity = np.asarray(self.ofc_data.sensitivity_matrix)

        np.testing.assert_array_equal(sensitivity[0, :, :], 0.0)
        np.testing.assert_array_equal(sensitivity[:, 0, :], 0.0)

        for piston_dof in (0, 5):
            response = sensitivity[:, :, piston_dof]
            peak_k, peak_j = np.unravel_index(np.argmax(np.abs(response)), response.shape)
            self.assertEqual(peak_k, 1)
            self.assertLess(peak_j, self.ofc_data.znmin)

    def test_matches_an_independently_built_decomposition(self) -> None:
        """The decomposition is the plain normalized SVD of the (k, j) slab.

        Pins the construction -- slab selection, right-side normalization and
        retention -- against the arithmetic written out directly, so a change
        in any of those three is caught here rather than downstream.
        """
        sensitivity = np.asarray(self.ofc_data.sensitivity_matrix)
        weights = np.asarray(self.ofc_data.normalization_weights)

        slab = sensitivity[K_MIN : K_MAX + 1][:, I_ZS, :]
        matrix = slab.reshape(-1, 50) @ np.diag(weights)
        u_expected, sigma_expected, vh_expected = np.linalg.svd(matrix, full_matrices=False)

        np.testing.assert_array_equal(self.estimator.Sigma, sigma_expected)
        np.testing.assert_array_equal(self.estimator.V, vh_expected.T)
        np.testing.assert_array_equal(self.estimator.U_eff, u_expected[:, :N_KEEP])

    def test_vmodes_are_amplitudes_over_sigma(self) -> None:
        """v-mode amplitudes are the u-mode amplitudes divided by sigma."""
        amplitudes = self.rng.normal(size=(7, N_KEEP))
        expected = amplitudes / self.estimator.Sigma[self.estimator.keep_idx][None, :]
        np.testing.assert_allclose(self.estimator.vmodes(amplitudes), expected)

    def test_dof_round_trip(self) -> None:
        """A state built from known DOF is recovered from its own wavefront.

        Only the retained subspace is recoverable, so the test projects the
        input into that subspace first rather than expecting an arbitrary state
        to survive truncation.
        """
        v_retained = self.estimator.V[:, self.estimator.keep_idx]
        sigma = self.estimator.Sigma[self.estimator.keep_idx]
        weights = self.estimator.normalization_weights

        coefficients = self.rng.normal(size=N_KEEP)
        dof_in = weights * (v_retained @ coefficients)

        wavefront = self.estimator.U_eff @ (sigma * coefficients)
        dof_out = self.estimator.dof(self.estimator.project_amplitudes(wavefront[None, :]))

        np.testing.assert_allclose(dof_out[0], dof_in, rtol=1e-9, atol=1e-12)

    def test_non_finite_wavefront_treated_as_zero(self) -> None:
        """NaN entries in the wavefront do not propagate into the state."""
        wavefront = self.rng.normal(size=(1, len(self.estimator.kj_grid)))
        with_nan = wavefront.copy()
        with_nan[0, 3] = np.nan
        zeroed = wavefront.copy()
        zeroed[0, 3] = 0.0

        np.testing.assert_array_equal(
            self.estimator.project_amplitudes(with_nan),
            self.estimator.project_amplitudes(zeroed),
        )

    def test_non_contiguous_n_keep(self) -> None:
        """An explicit mode list retains exactly those modes.

        The measured-intrinsic build uses this to drop individual v-modes from
        the middle of the spectrum, which a leading-n truncation index cannot
        express.
        """
        keep = [0, 1, 2, 5, 8, 13, 21, 33]
        estimator = DoubleZernikeStateEstimator(self.ofc_data, I_ZS, K_MIN, K_MAX, keep, n_dof=N_DOF)
        self.assertEqual(estimator.keep_idx, keep)
        self.assertEqual(estimator.n_keep_eff, len(keep))
        self.assertEqual(estimator.vmode_labels, [f"v{m + 1}" for m in keep])

        # The retained columns are the same vectors the full decomposition
        # holds at those indices, just gathered: the SVD does not change.
        full = DoubleZernikeStateEstimator(self.ofc_data, I_ZS, K_MIN, K_MAX, N_DOF, n_dof=N_DOF)
        np.testing.assert_array_equal(estimator.U_eff, full.U_eff[:, keep])
        np.testing.assert_array_equal(estimator.Sigma, full.Sigma)

    def test_n_keep_above_available_modes_is_clipped(self) -> None:
        """Asking for more modes than exist retains all of them."""
        estimator = DoubleZernikeStateEstimator(self.ofc_data, I_ZS, K_MIN, K_MAX, 500, n_dof=N_DOF)
        self.assertEqual(estimator.n_keep_eff, N_DOF)

    def test_reduced_dof_set(self) -> None:
        """An explicit DOF list restricts the state and its labels."""
        dof_idx = list(range(0, 10)) + list(range(10, 17)) + list(range(30, 35))
        estimator = DoubleZernikeStateEstimator(self.ofc_data, I_ZS, K_MIN, K_MAX, N_KEEP, n_dof=dof_idx)
        self.assertEqual(estimator.n_dof, len(dof_idx))
        self.assertEqual(estimator.dof_idx, dof_idx)

        labels, units = estimator.dof_labels()
        self.assertEqual(labels, [LABELS_50DOF[i] for i in dof_idx])
        self.assertEqual(units, [DOF_UNITS_50[i] for i in dof_idx])

    def test_explicit_normalization_weights(self) -> None:
        """Supplied weights are used instead of the configured ones.

        The operative weights are not always the ones the configuration names,
        so this path has to work for the estimator to reproduce a build.
        """
        weights = np.full(50, 2.0)
        estimator = DoubleZernikeStateEstimator(
            self.ofc_data,
            I_ZS,
            K_MIN,
            K_MAX,
            N_KEEP,
            n_dof=N_DOF,
            normalization_weights=weights,
        )
        np.testing.assert_array_equal(estimator.normalization_weights, weights)

    def test_dof_ranges_restricted_to_used_dof(self) -> None:
        """The range vector follows the used DOF subset."""
        dof_idx = [0, 1, 12, 21]
        estimator = DoubleZernikeStateEstimator(self.ofc_data, I_ZS, K_MIN, K_MAX, N_KEEP, n_dof=dof_idx)
        np.testing.assert_array_equal(estimator.dof_ranges(), self.ofc_data.dof_ranges()[dof_idx])

    def test_rejects_out_of_range_pupil_index(self) -> None:
        """A pupil Noll index off the end of the matrix raises."""
        with self.assertRaises(ValueError):
            DoubleZernikeStateEstimator(self.ofc_data, [4, 5, 999], K_MIN, K_MAX, N_KEEP)

    def test_rejects_inverted_k_range(self) -> None:
        """k_max below k_min raises."""
        with self.assertRaises(ValueError):
            DoubleZernikeStateEstimator(self.ofc_data, I_ZS, 6, 1, N_KEEP)

    def test_rejects_k_beyond_matrix(self) -> None:
        """A focal order off the end of the matrix raises."""
        n_k = np.asarray(self.ofc_data.sensitivity_matrix).shape[0]
        with self.assertRaises(ValueError):
            DoubleZernikeStateEstimator(self.ofc_data, I_ZS, 1, n_k + 5, N_KEEP)


if __name__ == "__main__":
    unittest.main()
