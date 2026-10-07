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
    "DoubleZernikeStateEstimator",
    "LABELS_50DOF",
    "DOF_UNITS_50",
]

import logging
from pathlib import Path

import numpy as np
import yaml

from .ofc_data import OFCData
from .range_bounded_recovery import (
    RBR_DEFAULT_KAPPA,
    RBR_DEFAULT_POWER,
    RBR_DEFAULT_WEIGHT,
    invert_range_penalty,
    wavefront_from_dof,
)

# 50-DOF state vector in the ts_ofc ordering: M2 hexapod (5), camera hexapod
# (5), M1M3 bending (20), M2 bending (20).
LABELS_50DOF = [
    "M2_dz",
    "M2_dx",
    "M2_dy",
    "M2_rx",
    "M2_ry",
    "Cam_dz",
    "Cam_dx",
    "Cam_dy",
    "Cam_rx",
    "Cam_ry",
    "B1_1",
    "B1_2",
    "B1_3",
    "B1_4",
    "B1_5",
    "B1_6",
    "B1_7",
    "B1_8",
    "B1_9",
    "B1_10",
    "B1_11",
    "B1_12",
    "B1_13",
    "B1_14",
    "B1_15",
    "B1_16",
    "B1_17",
    "B1_18",
    "B1_19",
    "B1_20",
    "B2_1",
    "B2_2",
    "B2_3",
    "B2_4",
    "B2_5",
    "B2_6",
    "B2_7",
    "B2_8",
    "B2_9",
    "B2_10",
    "B2_11",
    "B2_12",
    "B2_13",
    "B2_14",
    "B2_15",
    "B2_16",
    "B2_17",
    "B2_18",
    "B2_19",
    "B2_20",
]

# Unicode "μm" rather than ASCII "um": these strings are used directly as plot
# axis labels and as units in written tables.
DOF_UNITS_50 = (
    ["μm", "μm", "μm", "arcsec", "arcsec"]
    + ["μm", "μm", "μm", "arcsec", "arcsec"]
    + ["μm"] * 20
    + ["μm"] * 20
)


class DoubleZernikeStateEstimator:
    """Optical state estimator in the double-Zernike (DZ) basis.

    Estimates the optical state from double-Zernike wavefront coefficients,
    rather than from the wavefront at discrete sensor positions as
    `StateEstimator` does.

    The sensitivity matrix is a DZ slab: focal-field order ``k`` by pupil
    Zernike Noll index ``j`` by degree of freedom (DOF). This estimator
    decomposes a contiguous ``k`` range crossed with a chosen set of pupil
    Noll indices, which is the natural basis when the measurement is itself a
    DZ fit over the focal plane rather than a set of sensor readings.

    Parameters
    ----------
    ofc_data : `OFCData`
        Data container, supplying the sensitivity matrix, the DOF ordering and
        the allowed ranges.
    iZs : `list` of `int`
        Pupil Zernike Noll indices to retain, e.g. ``[4, 5, ..., 26]`` less any
        omitted terms. Need not be contiguous. These are Noll numbers used
        directly as pupil-axis indices, not offsets from ``znmin``.
    k_min : `int`
        First focal-field DZ order retained, inclusive. 1-based, so the
        field-constant term is ``k = 1``.
    k_max : `int`
        Last focal-field DZ order retained, inclusive.
    n_keep : `int` or `list` of `int`
        Modes retained. An `int` ``n`` keeps modes ``0..n-1``; a list keeps
        exactly those mode indices, which allows individual v-modes to be
        dropped from the middle of the spectrum.
    n_dof : `int` or `list` of `int` or `None`, optional
        DOF columns used. `None` uses all 50; an `int` ``n`` uses DOF
        ``0..n-1``; a list uses exactly those DOF indices.
    normalization_weights : `np.ndarray` or `str` or `Path` or `None`, optional
        Normalization weights ``w_j`` over all 50 DOF, as an array or a path to
        a yaml file holding one. `None` takes `OFCData.normalization_weights`.
        An explicit value is needed whenever the operative weights are not the
        ones the `OFCData` configuration names.
    log : `logging.Logger` or `None`, optional
        Logger. A new one is created if `None`.

    Attributes
    ----------
    U_eff : `np.ndarray`
        Left singular vectors of the retained modes, ``(n_kj, n_keep_eff)``.
    Sigma : `np.ndarray`
        Singular values, ``(n_modes,)``, in um of wavefront per normalized DOF.
    V : `np.ndarray`
        Right singular vectors, ``(n_dof, n_modes)`` — ``Vh.T``.
    normalization_weights : `np.ndarray`
        The weights ``w_j`` over the used DOF, ``(n_dof,)``.
    kj_grid : `list` of `tuple`
        ``(k, j)`` pair per row of the decomposed matrix, giving the order the
        wavefront vector ``W`` must be in.
    n_keep_eff : `int`
        Number of modes actually retained.
    keep_idx : `list` of `int`
        Retained mode indices.
    dof_idx : `list` of `int`
        Used DOF indices into the full 50.

    Notes
    -----
    The decomposition is of ``S @ diag(w)``, the sensitivity matrix normalized
    on the right, so the recovered normalized DOF are dimensionless and the
    singular values are comparable across DOF of different physical units. See
    Eqs 9-11 of https://ui.adsabs.harvard.edu/abs/2024ApJ...974..108M.

    This estimator and `StateEstimator` decompose the same underlying
    sensitivity matrix and agree closely: the DZ slab omits ``1.0e-05`` of the
    matrix power (dimensionless, squared Frobenius norm) for the ``k`` and
    ``j`` ranges the measured-intrinsic build uses. Individual v-modes past
    about mode 9 are nonetheless not comparable one-to-one between the two:
    the singular values cluster — several pairs within a few percent — which
    leaves the individual vectors inside a cluster basis-dependent while the
    spanned subspace is shared. Compare subspaces, not vectors, when relating
    the two.
    """

    def __init__(
        self,
        ofc_data: OFCData,
        iZs: list,
        k_min: int,
        k_max: int,
        n_keep: int | list,
        n_dof: int | list | None = None,
        normalization_weights: np.ndarray | str | Path | None = None,
        log: logging.Logger | None = None,
    ) -> None:
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        self.ofc_data = ofc_data
        self.k_min = int(k_min)
        self.k_max = int(k_max)
        self.iZs = [int(j) for j in iZs]

        weights_full = self._resolve_weights(normalization_weights)

        sensitivity_full = np.asarray(ofc_data.sensitivity_matrix)
        n_dof_full = sensitivity_full.shape[-1]

        # Both axes of the sensitivity matrix are 1-based index spaces with
        # entry 0 unused: pupil column j is Noll j, and focal row k is DZ order
        # k. So a Noll index is a column index directly -- do NOT offset by
        # znmin, which silently decomposes the wrong pupil terms.
        n_j_axis = sensitivity_full.shape[1]
        out_of_range = [j for j in self.iZs if j < 0 or j >= n_j_axis]
        if out_of_range:
            raise ValueError(
                f"Pupil Noll indices {out_of_range} are outside the "
                f"sensitivity matrix pupil axis (0-{n_j_axis - 1})."
            )
        j_cols = list(self.iZs)

        if self.k_max < self.k_min:
            raise ValueError(f"k_max ({self.k_max}) is below k_min ({self.k_min}).")
        if self.k_max >= sensitivity_full.shape[0]:
            raise ValueError(
                f"k_max ({self.k_max}) exceeds the available focal orders "
                f"(0-{sensitivity_full.shape[0] - 1})."
            )

        self.dof_idx = self._resolve_dof_idx(n_dof, n_dof_full)
        self.normalization_weights = weights_full[self.dof_idx]

        slab = sensitivity_full[self.k_min : self.k_max + 1][:, j_cols, :]
        matrix = slab.reshape(-1, n_dof_full)[:, self.dof_idx] @ np.diag(self.normalization_weights)

        self.kj_grid = [
            (int(self.k_min + k_offset), int(j))
            for k_offset in range(self.k_max - self.k_min + 1)
            for j in self.iZs
        ]

        U, Sigma, Vh = np.linalg.svd(matrix, full_matrices=False)
        self.Sigma = Sigma
        self.V = Vh.T

        n_modes = U.shape[1]
        if np.isscalar(n_keep):
            self.keep_idx = list(range(min(int(n_keep), n_modes)))
        else:
            self.keep_idx = sorted(k for k in (int(x) for x in n_keep) if k < n_modes)
        self.n_keep_eff = len(self.keep_idx)
        self.U_eff = U[:, self.keep_idx]

        self.vmode_labels = [f"v{m + 1}" for m in self.keep_idx]

    def _resolve_weights(self, normalization_weights: np.ndarray | str | Path | None) -> np.ndarray:
        """Resolve the 50-DOF weights from an array, a yaml path or the
        `OFCData` configuration.
        """
        if normalization_weights is None:
            return np.asarray(self.ofc_data.normalization_weights, dtype=float)
        if isinstance(normalization_weights, (str, Path)):
            with open(normalization_weights) as file_handle:
                return np.array(yaml.safe_load(file_handle), dtype=float)
        return np.asarray(normalization_weights, dtype=float)

    @staticmethod
    def _resolve_dof_idx(n_dof: int | list | None, n_dof_full: int) -> list:
        """Resolve the used DOF indices from `None`, a count or a list."""
        if n_dof is None:
            return list(range(n_dof_full))
        if np.isscalar(n_dof):
            return list(range(int(n_dof)))
        return sorted(int(d) for d in n_dof)

    @property
    def n_dof(self) -> int:
        """Number of degrees of freedom used."""
        return len(self.dof_idx)

    def project_amplitudes(self, wavefront: np.ndarray) -> np.ndarray:
        """Project DZ wavefront coefficients onto the retained u-modes.

        Parameters
        ----------
        wavefront : `np.ndarray`
            DZ coefficients, ``(n_visits, n_kj)`` in `kj_grid` order, in um of
            wavefront. Non-finite entries are treated as zero.

        Returns
        -------
        `np.ndarray`
            u-mode amplitudes ``A``, ``(n_visits, n_keep_eff)``, um of
            wavefront.
        """
        wavefront = np.asarray(wavefront, dtype=float)
        return np.where(np.isfinite(wavefront), wavefront, 0.0) @ self.U_eff

    def vmodes(self, amplitudes: np.ndarray) -> np.ndarray:
        """v-mode amplitudes from u-mode amplitudes.

        Parameters
        ----------
        amplitudes : `np.ndarray`
            u-mode amplitudes ``A``, ``(n_visits, n_keep_eff)``, um of
            wavefront.

        Returns
        -------
        `np.ndarray`
            v-mode amplitudes ``c_i = a_i / sigma_i``, dimensionless,
            ``(n_visits, n_keep_eff)``.
        """
        return np.asarray(amplitudes, dtype=float) / self.Sigma[self.keep_idx][None, :]

    def dof(self, amplitudes: np.ndarray) -> np.ndarray:
        """Physical DOF from u-mode amplitudes.

        With ``S = S_orig @ N`` normalized on the right and ``S = U Sigma
        V^T``, the recovery is ``dof = N V_eff diag(1 / sigma_eff) A``.
        Truncation is the only regularizer; see `dof_range_bounded` for the
        range-constrained recovery.

        Parameters
        ----------
        amplitudes : `np.ndarray`
            u-mode amplitudes ``A``, ``(n_visits, n_keep_eff)``, um of
            wavefront. Non-finite entries are treated as zero.

        Returns
        -------
        `np.ndarray`
            Physical DOF, ``(n_visits, n_dof)``, in the mixed units of
            `DOF_UNITS_50` over `dof_idx`.
        """
        amplitudes = np.asarray(amplitudes, dtype=float)
        amplitudes = np.where(np.isfinite(amplitudes), amplitudes, 0.0)

        v_eff = self.V[:, self.keep_idx]
        inv_sigma = 1.0 / self.Sigma[self.keep_idx]
        dof_normalized = (v_eff * inv_sigma[None, :]) @ amplitudes.T
        return (self.normalization_weights[:, None] * dof_normalized).T

    def dof_range_bounded(
        self,
        wavefront: np.ndarray,
        kappa: float | None = None,
        power: int | None = None,
        penalty_weight: float | None = None,
        full_dof: bool = False,
        return_info: bool = False,
        **kwargs: dict,
    ) -> np.ndarray | tuple:
        """Physical DOF under Range-Bounded Recovery (RBR).

        The range-constrained counterpart of `dof`. Each visit is solved
        independently, because the penalized inversion is nonlinear and so does
        not commute with any average over visits.

        Unlike `dof`, this takes the wavefront itself rather than u-mode
        amplitudes: the penalty acts on the physical DOF, so the solve cannot
        be expressed as a linear map applied after projection.

        Parameters
        ----------
        wavefront : `np.ndarray`
            DZ coefficients, ``(n_visits, n_kj)`` or ``(n_kj,)``, in `kj_grid`
            order, um of wavefront.
        kappa : `float` or `None`, optional
            Knee position as a multiple of the allowed range. `None` takes the
            controller configuration, falling back to `RBR_DEFAULT_KAPPA`.
        power : `int` or `None`, optional
            Penalty exponent ``p``, the penalty growing as ``|d_j| ** (2 p)``.
            `None` takes the controller configuration, falling back to
            `RBR_DEFAULT_POWER`.
        penalty_weight : `float` or `None`, optional
            Barrier weight ``lambda``, um**2 of wavefront. `None` takes the
            controller configuration key ``rbr_penalty_weight``, falling back
            to `RBR_DEFAULT_WEIGHT`.
        full_dof : `bool`, optional
            Solve over all used DOF with the barrier as the only regularizer,
            instead of restricting to the retained modes. The retained-mode
            solve couples the DOF, so bounding one that is far out of range
            drags others that are well inside theirs; see
            `invert_range_penalty` for why and for what this costs.
        return_info : `bool`, optional
            If `True`, also return the per-visit diagnostics `list` of `dict`.
        **kwargs : `dict`
            Passed through to `invert_range_penalty`.

        Returns
        -------
        dof : `np.ndarray`
            Physical DOF, ``(n_visits, n_dof)``, or ``(n_dof,)`` if a single
            wavefront was given.
        info : `list` of `dict`, optional
            Present when ``return_info``; one entry per visit.
        """
        if kappa is None:
            kappa = self.ofc_data.controller.get("rbr_kappa", RBR_DEFAULT_KAPPA)
        if power is None:
            power = self.ofc_data.controller.get("rbr_power", RBR_DEFAULT_POWER)
        if penalty_weight is None:
            penalty_weight = self.ofc_data.controller.get(
                "rbr_penalty_weight", RBR_DEFAULT_WEIGHT
            )

        wavefront = np.atleast_2d(np.asarray(wavefront, dtype=float))
        single = wavefront.shape[0] == 1

        ranges = self.dof_ranges()
        v_retained = None if full_dof else self.V[:, self.keep_idx]
        sigma_retained = self.Sigma[self.keep_idx]
        forward = self.forward_operator() if full_dof else None

        dof_out = np.empty((wavefront.shape[0], self.n_dof))
        info_out = []
        for visit in range(wavefront.shape[0]):
            result = invert_range_penalty(
                wavefront[visit],
                self.U_eff,
                sigma_retained,
                v_retained,
                self.normalization_weights,
                ranges,
                kappa=kappa,
                power=power,
                penalty_weight=penalty_weight,
                forward_operator=forward,
                return_info=True,
                **kwargs,
            )
            dof_out[visit], visit_info = result
            info_out.append(visit_info)

        if single:
            dof_out = dof_out[0]
        return (dof_out, info_out) if return_info else dof_out

    def wavefront_from_dof(self, dof: np.ndarray) -> np.ndarray:
        """DZ wavefront a recovered state reproduces.

        The forward map of `dof` and `dof_range_bounded`, for subtracting a
        recovered state from a measured wavefront. For an unregularized state
        this equals the orthogonal projection onto the retained u-modes; for a
        range-bounded one it does not.

        Parameters
        ----------
        dof : `np.ndarray`
            Physical DOF, ``(n_visits, n_dof)`` or ``(n_dof,)``, in the mixed
            units of `DOF_UNITS_50` over `dof_idx`.

        Returns
        -------
        `np.ndarray`
            DZ coefficients in `kj_grid` order, ``(n_visits, n_kj)`` or
            ``(n_kj,)``, um of wavefront.
        """
        return wavefront_from_dof(
            dof,
            self.U_eff,
            self.Sigma[self.keep_idx],
            self.V[:, self.keep_idx],
            self.normalization_weights,
        )

    def dof_labels(self) -> tuple:
        """Labels and units for the used DOF.

        Returns
        -------
        labels : `list` of `str`
            DOF names over `dof_idx`.
        units : `list` of `str`
            Unit per DOF, um or arcsec.
        """
        return (
            [LABELS_50DOF[i] for i in self.dof_idx],
            [DOF_UNITS_50[i] for i in self.dof_idx],
        )

    def dof_ranges(self) -> np.ndarray:
        """Return the allowed range per used DOF.

        Returns
        -------
        `np.ndarray`
            Allowed range ``r_j`` over `dof_idx`, um or arcsec per DOF — the
            full-50 vector from `OFCData.dof_ranges` restricted to the DOF this
            estimator uses.
        """
        return self.ofc_data.dof_ranges()[self.dof_idx]

    def forward_operator(self) -> np.ndarray:
        """Sensitivity per unit physical DOF, over the retained modes.

        Returns
        -------
        `np.ndarray`
            ``(n_kj, n_dof)``, um of wavefront per um or arcsec of DOF. Formed
            from the retained modes, so with every mode retained it is the full
            sensitivity and with a truncation it is the rank-limited one.

        Notes
        -----
        For `dof_range_bounded` with ``full_dof``, where the barrier replaces
        mode truncation as the regularizer and the solve needs the map in
        physical DOF rather than in retained mode coefficients.
        """
        sigma = self.Sigma[self.keep_idx]
        v_retained = self.V[:, self.keep_idx]
        normalized = self.U_eff @ (sigma[:, None] * v_retained.T)
        return normalized / self.normalization_weights[None, :]
