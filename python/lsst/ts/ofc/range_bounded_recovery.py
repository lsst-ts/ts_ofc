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

__all__ = [
    "RBR_DEFAULT_KAPPA",
    "RBR_DEFAULT_POWER",
    "RBR_DEFAULT_WEIGHT",
    "achieved_residual",
    "invert_range_penalty",
    "invert_truncated",
    "wavefront_from_dof",
]

import numpy as np

# The penalty reaches unity at |d_j| = RBR_DEFAULT_KAPPA * r_j, and grows as
# |d_j| ** (2 * RBR_DEFAULT_POWER).
RBR_DEFAULT_KAPPA = 4.0
RBR_DEFAULT_POWER = 3

# Weight on the barrier relative to the data term, um**2 of wavefront.  The
# barrier is dimensionless and the data term is um**2 of wavefront, so the two
# are commensurate only through this weight.  1.0 is what the paired-difference
# studies ran at before the weight was named; it is the right scale when the
# input wavefront puts the worst DOF around ten times its range, and far too
# strong when it puts it around fifty (see the module notes).
RBR_DEFAULT_WEIGHT = 1.0


def invert_truncated(
    wavefront: np.ndarray,
    u_eff: np.ndarray,
    sigma: np.ndarray,
    v_retained: np.ndarray,
    normalization_weights: np.ndarray,
) -> np.ndarray:
    """Recover degrees of freedom (DOF) by truncated-SVD inversion.

    The unregularized recovery, in which truncation is the only regularizer.

    Parameters
    ----------
    wavefront : `np.ndarray`
        Measured wavefront, ``(n_kj,)``, um of wavefront. Non-finite entries
        are treated as zero.
    u_eff : `np.ndarray`
        Left singular vectors of the retained modes, ``(n_kj, n_keep)``.
    sigma : `np.ndarray`
        Singular values of the retained modes, ``(n_keep,)``.
    v_retained : `np.ndarray`
        Right singular vectors of the retained modes, ``(n_dof, n_keep)``.
    normalization_weights : `np.ndarray`
        Weights ``w_j``, ``(n_dof,)``.

    Returns
    -------
    `np.ndarray`
        Physical DOF, ``(n_dof,)``, um or arcsec per DOF.
    """
    wavefront = np.nan_to_num(np.asarray(wavefront, dtype=float))
    amplitudes = u_eff.T @ wavefront
    return normalization_weights * (v_retained @ (amplitudes / sigma))


def wavefront_from_dof(
    dof: np.ndarray,
    u_eff: np.ndarray,
    sigma: np.ndarray,
    v_retained: np.ndarray,
    normalization_weights: np.ndarray,
) -> np.ndarray:
    """Wavefront a recovered state reproduces, through the rank-limited operator.

    The forward direction of `invert_truncated` and `invert_range_penalty`:
    ``dW = U Sigma V^T N^-1 d``, restricted to the retained modes. This is what
    a build subtracts to remove a recovered state from a measured wavefront.

    Applied to `invert_truncated`'s output this reduces to the orthogonal
    projection ``U_eff @ (U_eff.T @ dW)``, so an unregularized recovery
    subtracts exactly the retained-subspace projection. A range-bounded state
    does not, which is the point: it cannot reach parts of that subspace that
    need out-of-range motion.

    Parameters
    ----------
    dof : `np.ndarray`
        Physical DOF, ``(n_dof,)`` or ``(n_visits, n_dof)``, um or arcsec
        per DOF.
    u_eff : `np.ndarray`
        Left singular vectors of the retained modes, ``(n_kj, n_keep)``.
    sigma : `np.ndarray`
        Singular values of the retained modes, ``(n_keep,)``.
    v_retained : `np.ndarray`
        Right singular vectors of the retained modes, ``(n_dof, n_keep)``.
    normalization_weights : `np.ndarray`
        Weights ``w_j``, ``(n_dof,)``.

    Returns
    -------
    `np.ndarray`
        Wavefront, ``(n_kj,)`` or ``(n_visits, n_kj)``, um of wavefront.
    """
    normalized_dof = np.asarray(dof, dtype=float) / normalization_weights
    return np.einsum("kn,n,dn,...d->...k", u_eff, sigma, v_retained, normalized_dof)


def achieved_residual(
    wavefront: np.ndarray,
    dof: np.ndarray,
    u_eff: np.ndarray,
    sigma: np.ndarray,
    v_retained: np.ndarray,
    normalization_weights: np.ndarray,
) -> float:
    """Root-mean-square wavefront left unexplained by a recovered state.

    The residual actually achieved, ``|| dW - S d ||`` evaluated through the
    same rank-limited operator the recovery used. This is the metric for
    comparing a regularized recovery against an unregularized one: a projection
    onto the retained subspace would instead credit the regularized solution
    with wavefront it does not reproduce.

    Parameters
    ----------
    wavefront : `np.ndarray`
        Measured wavefront, ``(n_kj,)``, um of wavefront.
    dof : `np.ndarray`
        Recovered physical DOF, ``(n_dof,)``, um or arcsec per DOF.
    u_eff : `np.ndarray`
        Left singular vectors of the retained modes, ``(n_kj, n_keep)``.
    sigma : `np.ndarray`
        Singular values of the retained modes, ``(n_keep,)``.
    v_retained : `np.ndarray`
        Right singular vectors of the retained modes, ``(n_dof, n_keep)``.
    normalization_weights : `np.ndarray`
        Weights ``w_j``, ``(n_dof,)``.

    Returns
    -------
    `float`
        Root-mean-square of the residual, um of wavefront.
    """
    wavefront = np.nan_to_num(np.asarray(wavefront, dtype=float))
    predicted = wavefront_from_dof(
        dof, u_eff, sigma, v_retained, normalization_weights
    )
    residual = wavefront - predicted
    return float(np.sqrt(np.mean(residual**2)))


def invert_range_penalty(
    wavefront: np.ndarray,
    u_eff: np.ndarray,
    sigma: np.ndarray,
    v_retained: np.ndarray | None,
    normalization_weights: np.ndarray,
    ranges: np.ndarray,
    *,
    kappa: float = RBR_DEFAULT_KAPPA,
    power: int = RBR_DEFAULT_POWER,
    penalty_weight: float = RBR_DEFAULT_WEIGHT,
    forward_operator: np.ndarray | None = None,
    tikhonov: float = 0.0,
    n_iter: int = 200,
    tol: float = 1e-10,
    eps: float = 1e-12,
    relax: float = 1.0,
    return_info: bool = False,
) -> np.ndarray | tuple:
    """Range-Bounded Recovery (RBR) of the optical state.

    Recovers degrees of freedom (DOF) under a superlinear per-DOF penalty on
    leaving the allowed range, so the recovered state stays within the stroke
    the hexapods and mirrors can physically reach. Minimizes, over normalized
    DOF ``x`` with physical ``d = w * x``::

        || dW - S x ||**2  +  tikhonov**2 * || x ||**2
            +  lambda * sum_j ( |d_j| / (kappa * r_j) ) ** (2 * power)

    The penalty is far below unity while ``|d_j| / r_j`` stays under ``kappa``
    and rises steeply as the ratio approaches and passes it. It is therefore a
    barrier, not a shrinkage term: it leaves a DOF comfortably inside its range
    essentially untouched, unlike a quadratic penalty which pulls on every DOF
    everywhere.

    The barrier sum is dimensionless and the data term is um**2 of wavefront,
    so ``lambda`` (``penalty_weight``) carries um**2 of wavefront and sets how
    the two compare. It matters: because the barrier grows as the ratio to the
    ``2 p`` power, an input wavefront whose worst DOF sits at fifty times its
    range rather than ten produces a barrier some six orders of magnitude
    larger, and at ``lambda = 1`` that swamps the data term entirely.

    Parameters
    ----------
    wavefront : `np.ndarray`
        Measured wavefront, ``(n_kj,)``, um of wavefront. Non-finite entries
        are treated as zero.
    u_eff : `np.ndarray`
        Left singular vectors of the retained modes, ``(n_kj, n_keep)``.
    sigma : `np.ndarray`
        Singular values of the retained modes, ``(n_keep,)``.
    v_retained : `np.ndarray` or `None`
        Right singular vectors of the retained modes, ``(n_dof, n_keep)``.
        Ignored, and may be `None`, when ``forward_operator`` is given.
    normalization_weights : `np.ndarray`
        Weights ``w_j``, ``(n_dof,)``.
    ranges : `np.ndarray`
        Allowed range ``r_j``, ``(n_dof,)``, um or arcsec per DOF, from
        `OFCData.dof_ranges`. Must be strictly positive and finite.
    kappa : `float`, optional
        Dimensionless knee position as a multiple of the range: the penalty
        reaches unity at ``|d_j| = kappa * r_j``.
    power : `int`, optional
        Penalty exponent ``p``; the penalty grows as ``|d_j| ** (2 * p)``, so
        ``p = 1`` is Tikhonov on ``d_j / r_j`` and larger ``p`` leaves the
        sub-knee region progressively freer.
    penalty_weight : `float`, optional
        Weight ``lambda`` on the barrier, um**2 of wavefront, which is what
        makes it commensurate with the data term. Scaling it is equivalent to
        moving the knee, since ``lambda * (t / kappa) ** (2 p)`` equals
        ``(t / kappa_eff) ** (2 p)`` with
        ``kappa_eff = kappa * lambda ** (-1 / (2 p))``, but it is the better
        conditioned of the two knobs.
    forward_operator : `np.ndarray` or `None`, optional
        Sensitivity in um of wavefront per unit *physical* DOF,
        ``(n_kj, n_dof)``. When given, the solve runs over all ``n_dof``
        physical DOF with the barrier as the only regularizer, and
        ``v_retained`` is ignored; when `None`, the solve is restricted to the
        retained modes. See the Notes for when each is appropriate.
    tikhonov : `float`, optional
        Optional Tikhonov floor on ``x``, in singular-value units, to keep the
        normal equations well posed if the retained rank exposes near-null
        modes.
    n_iter : `int`, optional
        Maximum iteratively reweighted least squares (IRLS) iterations.
    tol : `float`, optional
        Convergence tolerance on the relative change of ``d`` between
        iterations, dimensionless.
    eps : `float`, optional
        Floor on ``|d_j|`` inside the reweighting, in DOF units, so a DOF
        landing exactly at zero does not divide by zero.
    relax : `float`, optional
        Initial IRLS step fraction in (0, 1]. Backtracking makes the iteration
        monotone regardless, so this is a starting guess rather than a knob
        needing tuning per ``power``.
    return_info : `bool`, optional
        If `True`, also return a diagnostics `dict`.

    Returns
    -------
    dof : `np.ndarray`
        Physical DOF, ``(n_dof,)``, um or arcsec per DOF.
    info : `dict`, optional
        Present when ``return_info``. Keys ``n_iter`` (`int`), ``converged``
        (`bool`), ``delta`` (`float`, final relative change, dimensionless),
        ``max_ratio`` (`float`, largest ``|d_j| / r_j``, dimensionless) and
        ``objective`` (`float`, final objective, um of wavefront squared).

    Notes
    -----
    IRLS linearizes the penalty as a quadratic ``sum_j q_j d_j**2`` whose
    weight is recomputed from the previous iterate::

        q_j = (kappa * r_j) ** (-2 p) * |d_j| ** (2 p - 2)

    so each iteration is one symmetric solve. Two details are load-bearing and
    were established by measurement rather than by derivation:

    The solve is done in the retained mode coefficients ``b`` with ``x = V_r
    b`` rather than in ``x`` directly. The rank-limited operator leaves
    ``n_dof - n_keep`` null directions in which a solve in ``x`` returns noise,
    whereas the truncated solution sets them to zero; restricting to ``V_r``
    reproduces that choice, so the penalty-off limit returns the truncated
    answer exactly. In that basis the data term is diagonal, so each iteration
    costs one ``n_keep`` by ``n_keep`` solve.

    **That restriction couples the DOF, which is why ``forward_operator``
    exists.** With ``d`` confined to the ``n_keep``-dimensional column space of
    ``V_r``, no DOF can move independently of the others. Bounding one DOF that
    sits far outside its range therefore drags every DOF sharing those mode
    directions, including ones whose own barrier term is negligible -- a
    hexapod piston at a tenth of its range gets pulled by orders of magnitude
    while contributing a penalty around 1e-10. The pulled DOF are not being
    penalized; they are being reparametrized. A per-DOF ``lambda`` does not fix
    this, because the coupling is in the parametrization and not in the
    penalty.

    Passing ``forward_operator`` instead solves over all ``n_dof`` physical DOF
    with no mode truncation, letting the barrier be the only regularizer. Each
    DOF is then free, and one comfortably inside its range stays where the data
    puts it. Use this when the input wavefront drives some DOF far outside
    range; use the retained-mode form when the penalty-off limit must reproduce
    a truncated scheme exactly.

    Two properties of the full-DOF form are worth knowing. It has no truncated
    solution to start from, so it starts cold at ``d = 0``. And because the
    barrier is very flat below the knee, its objective has a broad shallow
    basin: different starts reach DOF differing by a few tenths of ``r_j``
    while the wavefront ``S d`` they produce agrees to well under a percent.
    The recovered wavefront is therefore reliable and the recovered DOF are not
    a unique optical state -- fine for subtracting a wavefront, not for
    quoting an amplitude.

    Each step is backtracked until the objective decreases. For ``power >= 2``
    the objective is convex in ``b``, but the reweighting is only a local model
    and a full step can overshoot: at ``power = 3`` a fixed half-step enters a
    limit cycle that never converges, stalling at a relative change of 1.6e-02
    and returning a largest ``|d_j| / r_j`` of 0.585 against the converged
    0.537. Backtracking makes the iteration monotone and convergent for every
    ``power`` tested, and removes the step size as a tuning knob.
    """
    wavefront = np.nan_to_num(np.asarray(wavefront, dtype=float))
    range_vector = np.asarray(ranges, dtype=float)
    if np.any(~np.isfinite(range_vector)) or np.any(range_vector <= 0):
        raise ValueError(
            "Range-Bounded Recovery needs strictly positive finite ranges; "
            "got non-positive or non-finite entries."
        )

    weights = np.asarray(normalization_weights, dtype=float)
    exponent = int(power)
    # DOF units; the penalty equals unity here.
    scale = float(kappa) * range_vector

    lam = float(penalty_weight)
    full_dof = forward_operator is not None
    if full_dof:
        # Solve over all n_dof physical DOF, with the barrier as the only
        # regularizer, so there is no retained-mode basis to restrict to.
        forward = np.asarray(forward_operator, dtype=float)
        gram = forward.T @ forward
        normal_rhs = forward.T @ wavefront
    else:
        sigma_squared = sigma**2
        rhs = sigma * (u_eff.T @ wavefront)
        # d = weighted_v @ b maps retained mode coefficients to physical DOF.
        weighted_v = weights[:, None] * v_retained

    def objective(dof_trial: np.ndarray) -> float:
        """Penalized least-squares objective, um of wavefront squared."""
        if full_dof:
            misfit = wavefront - forward @ dof_trial
            ridge = 0.0
        else:
            coefficients = np.linalg.lstsq(weighted_v, dof_trial, rcond=None)[0]
            misfit = wavefront - u_eff @ (sigma * coefficients)
            ridge = float(tikhonov) ** 2 * float(coefficients @ coefficients)
        return (
            float(misfit @ misfit)
            + ridge
            + lam * float(np.sum((np.abs(dof_trial) / scale) ** (2 * exponent)))
        )

    if full_dof:
        # The truncated solution is not available without a retained basis, and
        # a cold start is the neutral choice.  The barrier basin is broad below
        # the knee, so the recovered DOF depend weakly on the start even though
        # the wavefront they produce does not; see the Notes.
        dof = np.zeros(forward.shape[1])
    else:
        dof = invert_truncated(wavefront, u_eff, sigma, v_retained, weights)
    current_objective = objective(dof)
    converged, used_iterations, relative_change = False, 0, np.inf

    for iteration in range(int(n_iter)):
        used_iterations = iteration + 1
        magnitude = np.maximum(np.abs(dof), eps)
        # Penalty curvature in DOF units.
        curvature = lam * scale ** (-2 * exponent) * magnitude ** (2 * exponent - 2)
        if full_dof:
            dof_full_step = np.linalg.solve(gram + np.diag(curvature), normal_rhs)
        else:
            normal_matrix = np.diag(
                sigma_squared + float(tikhonov) ** 2
            ) + weighted_v.T @ (curvature[:, None] * weighted_v)
            coefficients = np.linalg.solve(normal_matrix, rhs)
            dof_full_step = weighted_v @ coefficients

        step = float(relax)
        for _ in range(40):
            candidate = dof + step * (dof_full_step - dof)
            candidate_objective = objective(candidate)
            if candidate_objective <= current_objective:
                break
            step *= 0.5
        else:
            # No downhill step remains, so this is a minimum.
            converged = True
            break

        denominator = max(float(np.max(np.abs(dof))), eps)
        relative_change = float(np.max(np.abs(candidate - dof)) / denominator)
        dof, current_objective = candidate, candidate_objective
        if relative_change < float(tol):
            converged = True
            break

    if return_info:
        return dof, dict(
            n_iter=used_iterations,
            converged=converged,
            delta=relative_change,
            max_ratio=float(np.max(np.abs(dof) / range_vector)),
            objective=float(current_objective),
        )
    return dof
