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
from typing import Any

import numpy as np

from lsst.ts.ofc import (
    RBR_DEFAULT_KAPPA,
    RBR_DEFAULT_POWER,
    RBR_DEFAULT_WEIGHT,
    DoubleZernikeStateEstimator,
    OFCData,
    achieved_residual,
    invert_range_penalty,
    invert_truncated,
    wavefront_from_dof,
)

I_ZS = [j for j in range(4, 27) if j not in (20, 21)]
K_MIN = 1
K_MAX = 6
N_KEEP = 34
N_DOF = 50

# Allowed ranges r_j that the shipped normalization weights were generated
# with, in each DOF's own unit. Pinned so a change to the stroke or force-range
# configuration is visible here rather than silently rescaling the penalty.
EXPECTED_RANGES = {
    0: (5900.0, "um, M2 piston"),
    1: (6700.0, "um, M2 decenter y"),
    3: (0.12, "arcsec, M2 tilt x"),
    12: (0.0877126, "um, M1M3 bending mode 3"),
    21: (0.00908752, "um, M1M3 bending mode 12"),
}


class TestRangeBoundedRecovery(unittest.TestCase):
    """Test Range-Bounded Recovery and the allowed-range vector."""

    def setUp(self) -> None:
        self.ofc_data = OFCData("lsst")
        self.estimator = DoubleZernikeStateEstimator(self.ofc_data, I_ZS, K_MIN, K_MAX, N_KEEP, n_dof=N_DOF)
        self.v_retained = self.estimator.V[:, self.estimator.keep_idx]
        self.sigma = self.estimator.Sigma[self.estimator.keep_idx]
        self.weights = self.estimator.normalization_weights
        self.ranges = self.estimator.dof_ranges()

        # Scaled so the unregularized solution lands well outside the allowed
        # range on the stiff bending modes, which is the regime RBR exists for.
        self.rng = np.random.default_rng(11)
        self.wavefront = self.rng.normal(scale=0.05, size=len(self.estimator.kj_grid))

    def solve_truncated(self) -> np.ndarray:
        return invert_truncated(
            self.wavefront, self.estimator.U_eff, self.sigma, self.v_retained, self.weights
        )

    def solve_rbr(self, **kwargs: Any) -> Any:
        return invert_range_penalty(
            self.wavefront,
            self.estimator.U_eff,
            self.sigma,
            self.v_retained,
            self.weights,
            self.ranges,
            **kwargs,
        )

    def test_dof_ranges_values(self) -> None:
        """The allowed ranges are the configured strokes and force ranges."""
        ranges = self.ofc_data.dof_ranges()
        self.assertEqual(ranges.shape, (50,))
        for index, (expected, description) in EXPECTED_RANGES.items():
            self.assertAlmostEqual(
                ranges[index],
                expected,
                places=6,
                msg=f"DOF {index} ({description})",
            )

    def test_dof_ranges_all_positive(self) -> None:
        """Every range is strictly positive, as the penalty divides by it."""
        ranges = self.ofc_data.dof_ranges()
        self.assertTrue(np.all(np.isfinite(ranges)))
        self.assertTrue(np.all(ranges > 0))

    def test_rigid_body_ranges_far_exceed_bending(self) -> None:
        """Hexapod strokes are orders of magnitude above bending amplitudes.

        This is why the penalty normalizes per DOF: an unnormalized bound could
        not hold micrometre-scale hexapod motion and sub-micrometre bending
        amplitudes in the same expression.
        """
        ranges = self.ofc_data.dof_ranges()
        self.assertGreater(np.min(ranges[:3]), 1e3)
        self.assertLess(np.max(ranges[10:50]), 1e1)

    def test_penalty_off_limit_is_truncated(self) -> None:
        """A knee pushed to infinity returns the unregularized solution.

        Guards the choice to solve in the retained mode coefficients: a solve
        in the DOF basis would fill the discarded null directions with noise
        and fail this.
        """
        np.testing.assert_allclose(self.solve_rbr(kappa=1e12), self.solve_truncated(), rtol=1e-9, atol=1e-12)

    def test_reduces_the_range_excess(self) -> None:
        """RBR brings the worst over-range DOF far closer to its range."""
        truncated_ratio = np.max(np.abs(self.solve_truncated()) / self.ranges)
        _, info = self.solve_rbr(return_info=True)

        self.assertGreater(truncated_ratio, 10.0)
        self.assertLess(info["max_ratio"], truncated_ratio)
        self.assertLess(info["max_ratio"], RBR_DEFAULT_KAPPA)

    def test_converges_at_default_power(self) -> None:
        """The iteration converges at the steep default exponent.

        A fixed step size does not: at power 3 it enters a limit cycle. The
        backtracking line search is what makes this pass.
        """
        _, info = self.solve_rbr(return_info=True)
        self.assertTrue(info["converged"])
        self.assertLess(info["n_iter"], 200)

    def test_objective_decreases_monotonically(self) -> None:
        """Each additional iteration leaves the objective no worse.

        Run with a rising iteration cap rather than by instrumenting the
        solver, so the property is checked through the public interface.
        """
        objectives = []
        for n_iter in range(1, 8):
            _, info = self.solve_rbr(n_iter=n_iter, return_info=True)
            objectives.append(info["objective"])

        for earlier, later in zip(objectives, objectives[1:]):
            self.assertLessEqual(later, earlier + 1e-12)

    def test_stronger_penalty_binds_harder(self) -> None:
        """A tighter knee yields a state further inside the allowed range."""
        ratios = []
        for kappa in (16.0, 4.0, 1.0):
            _, info = self.solve_rbr(kappa=kappa, return_info=True)
            ratios.append(info["max_ratio"])

        for looser, tighter in zip(ratios, ratios[1:]):
            self.assertLess(tighter, looser)

    def test_residual_cost_is_bounded(self) -> None:
        """The wavefront given up for the range bound stays modest.

        RBR must degrade the achieved residual -- it is solving a constrained
        problem -- but a bound that cost most of the fit would not be usable.
        """
        truncated = self.solve_truncated()
        bounded = self.solve_rbr()

        residual_truncated = achieved_residual(
            self.wavefront,
            truncated,
            self.estimator.U_eff,
            self.sigma,
            self.v_retained,
            self.weights,
        )
        residual_bounded = achieved_residual(
            self.wavefront,
            bounded,
            self.estimator.U_eff,
            self.sigma,
            self.v_retained,
            self.weights,
        )

        self.assertGreaterEqual(residual_bounded, residual_truncated)
        self.assertLess(residual_bounded, 1.5 * residual_truncated)

    def test_achieved_residual_zero_for_exact_state(self) -> None:
        """A state that reproduces the wavefront leaves no residual."""
        coefficients = self.rng.normal(size=N_KEEP)
        wavefront = self.estimator.U_eff @ (self.sigma * coefficients)
        dof = self.weights * (self.v_retained @ coefficients)

        residual = achieved_residual(
            wavefront,
            dof,
            self.estimator.U_eff,
            self.sigma,
            self.v_retained,
            self.weights,
        )
        self.assertLess(residual, 1e-10)

    def test_rejects_non_positive_ranges(self) -> None:
        """A zero or negative range raises rather than dividing by zero."""
        bad = self.ranges.copy()
        bad[5] = 0.0
        with self.assertRaises(ValueError):
            invert_range_penalty(
                self.wavefront,
                self.estimator.U_eff,
                self.sigma,
                self.v_retained,
                self.weights,
                bad,
            )

    def test_default_weight_reproduces_the_unweighted_barrier(self) -> None:
        """The default weight is the value the unweighted barrier had.

        Pins backward compatibility: the paired-difference studies ran with the
        barrier at an implicit weight of 1, so the default must leave their
        results unchanged.
        """
        self.assertEqual(RBR_DEFAULT_WEIGHT, 1.0)
        np.testing.assert_allclose(
            self.solve_rbr(penalty_weight=1.0), self.solve_rbr(), rtol=1e-12, atol=1e-14
        )

    def test_weight_is_equivalent_to_moving_the_knee(self) -> None:
        """Scaling the weight equals rescaling kappa by lambda**(-1/(2p)).

        The two knobs are the same knob. Documented on
        `invert_range_penalty`, and relied on when choosing a weight, so it is
        pinned rather than left as an identity in prose.
        """
        weight, power = 1e-4, RBR_DEFAULT_POWER
        kappa_equivalent = RBR_DEFAULT_KAPPA * weight ** (-1.0 / (2 * power))
        np.testing.assert_allclose(
            self.solve_rbr(penalty_weight=weight, power=power),
            self.solve_rbr(kappa=kappa_equivalent, power=power),
            rtol=1e-7,
            atol=1e-9,
        )

    def test_weaker_weight_bounds_less(self) -> None:
        """A smaller weight leaves the state further outside the range."""
        _, strong = self.solve_rbr(penalty_weight=1.0, return_info=True)
        _, weak = self.solve_rbr(penalty_weight=1e-6, return_info=True)
        self.assertGreater(weak["max_ratio"], strong["max_ratio"])

    def test_full_dof_spans_directions_the_retained_solve_cannot(self) -> None:
        """The full-DOF solve is not confined to the retained-mode subspace.

        This is the structural difference the mode exists for. The
        retained-mode solve returns ``d = (w . V_r) b``, so every solution lies
        in a ``n_keep``-dimensional subspace and no DOF can move independently
        of the others; the full-DOF solve has all ``n_dof`` directions
        available.

        What that coupling costs on real data is not asserted here. It depends
        on the measured wavefront -- on the MIW it crushes hexapod DOF sitting
        at a tenth of their range -- and it is not reproducible from a
        synthetic input, because the truncated inverse redistributes an
        injected state rather than returning it.
        """
        forward = self.estimator.forward_operator()
        retained = self.solve_rbr()
        full = invert_range_penalty(
            self.wavefront,
            self.estimator.U_eff,
            self.sigma,
            None,
            self.weights,
            self.ranges,
            forward_operator=forward,
        )

        # The retained solve lies in the span of (w . V_r); the full one
        # need not.
        basis = self.weights[:, None] * self.v_retained
        projector = basis @ np.linalg.pinv(basis)
        residual_retained = np.linalg.norm(retained - projector @ retained)
        residual_full = np.linalg.norm(full - projector @ full)
        self.assertLess(residual_retained / np.linalg.norm(retained), 1e-10)
        self.assertGreater(residual_full / np.linalg.norm(full), 1e-3)

    def test_full_dof_bounds_the_range_excess(self) -> None:
        """The barrier alone bounds the state, with no mode truncation."""
        truncated_ratio = np.max(np.abs(self.solve_truncated()) / self.ranges)
        full, info = invert_range_penalty(
            self.wavefront,
            self.estimator.U_eff,
            self.sigma,
            None,
            self.weights,
            self.ranges,
            forward_operator=self.estimator.forward_operator(),
            return_info=True,
        )
        self.assertGreater(truncated_ratio, 10.0)
        self.assertLess(info["max_ratio"], truncated_ratio)
        self.assertLess(info["max_ratio"], RBR_DEFAULT_KAPPA)
        self.assertTrue(info["converged"])

    def test_full_dof_needs_no_retained_basis(self) -> None:
        """`v_retained` may be None when a forward operator is given."""
        full = invert_range_penalty(
            self.wavefront,
            self.estimator.U_eff,
            self.sigma,
            None,
            self.weights,
            self.ranges,
            forward_operator=self.estimator.forward_operator(),
        )
        self.assertEqual(full.shape, (N_DOF,))
        self.assertTrue(np.all(np.isfinite(full)))

    def test_forward_operator_matches_the_forward_map(self) -> None:
        """`forward_operator` applied to DOF is `wavefront_from_dof`."""
        dof = self.rng.normal(size=N_DOF)
        np.testing.assert_allclose(
            self.estimator.forward_operator() @ dof,
            self.estimator.wavefront_from_dof(dof),
            rtol=1e-9,
            atol=1e-12,
        )

    def test_estimator_full_dof_matches_the_solver(self) -> None:
        """`dof_range_bounded(full_dof=True)` is the full-DOF solver."""
        direct = invert_range_penalty(
            self.wavefront,
            self.estimator.U_eff,
            self.sigma,
            None,
            self.weights,
            self.ranges,
            forward_operator=self.estimator.forward_operator(),
        )
        through_estimator = self.estimator.dof_range_bounded(self.wavefront, full_dof=True)
        np.testing.assert_allclose(through_estimator, direct, rtol=1e-12, atol=1e-14)

    def test_estimator_method_matches_the_solver(self) -> None:
        """`dof_range_bounded` is the solver applied per visit."""
        direct = self.solve_rbr()
        through_estimator = self.estimator.dof_range_bounded(self.wavefront)
        np.testing.assert_allclose(through_estimator, direct, rtol=1e-12, atol=1e-14)

    def test_estimator_method_handles_several_visits(self) -> None:
        """Each visit is solved independently.

        The inversion is nonlinear, so it does not commute with any average
        over visits and cannot be applied to a stacked mean.
        """
        wavefronts = self.rng.normal(scale=0.05, size=(3, len(self.estimator.kj_grid)))
        states, info = self.estimator.dof_range_bounded(wavefronts, return_info=True)

        self.assertEqual(states.shape, (3, N_DOF))
        self.assertEqual(len(info), 3)
        for visit in range(3):
            expected = invert_range_penalty(
                wavefronts[visit],
                self.estimator.U_eff,
                self.sigma,
                self.v_retained,
                self.weights,
                self.ranges,
            )
            np.testing.assert_allclose(states[visit], expected, rtol=1e-12, atol=1e-14)

    def forward(self, dof: np.ndarray) -> np.ndarray:
        return wavefront_from_dof(dof, self.estimator.U_eff, self.sigma, self.v_retained, self.weights)

    def test_forward_map_of_truncated_is_the_umode_projection(self) -> None:
        """An unregularized state reproduces the retained-subspace projection.

        This is the identity that makes Range-Bounded Recovery a drop-in for a
        build that currently subtracts ``U_eff @ (U_eff.T @ dW)``: with the
        penalty off, the two agree. They agree numerically, not bit for bit --
        the round trip through physical DOF associates the products
        differently -- so a caller needing an exactly reproducible
        unconstrained result must keep using the direct projection.
        """
        projection = self.estimator.U_eff @ (self.estimator.U_eff.T @ self.wavefront)
        np.testing.assert_allclose(self.forward(self.solve_truncated()), projection, rtol=1e-9, atol=1e-13)

    def test_forward_map_inverts_the_recovery(self) -> None:
        """Recovering from a forward-mapped state returns that state.

        True only for a state already inside the retained row space, which the
        recovered one is by construction.
        """
        dof = self.solve_truncated()
        recovered = invert_truncated(
            self.forward(dof),
            self.estimator.U_eff,
            self.sigma,
            self.v_retained,
            self.weights,
        )
        np.testing.assert_allclose(recovered, dof, rtol=1e-8, atol=1e-12)

    def test_forward_map_of_range_bounded_differs(self) -> None:
        """A range-bounded state does not reproduce the full projection.

        The point of the constraint: wavefront needing out-of-range motion is
        left in the residual rather than removed.
        """
        projection = self.estimator.U_eff @ (self.estimator.U_eff.T @ self.wavefront)
        bounded = self.forward(self.solve_rbr())
        self.assertGreater(float(np.sqrt(np.mean((bounded - projection) ** 2))), 1e-4)

    def test_forward_map_batches_over_visits(self) -> None:
        """A stack of states maps row by row."""
        states = np.stack([self.solve_truncated(), self.solve_rbr()])
        batched = self.forward(states)
        self.assertEqual(batched.shape, (2, len(self.estimator.kj_grid)))
        for visit in range(2):
            np.testing.assert_allclose(batched[visit], self.forward(states[visit]))

    def test_estimator_forward_map_matches_the_function(self) -> None:
        """The estimator method is the free function with its own arrays."""
        dof = self.solve_rbr()
        np.testing.assert_array_equal(self.estimator.wavefront_from_dof(dof), self.forward(dof))

    def test_defaults_are_the_documented_pair(self) -> None:
        """Check the defaults are the settled knee and exponent."""
        self.assertEqual(RBR_DEFAULT_KAPPA, 4.0)
        self.assertEqual(RBR_DEFAULT_POWER, 3)


if __name__ == "__main__":
    unittest.main()
