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

import argparse
from pathlib import Path

import numpy as np
import yaml

from lsst.ts.wep.utils import convertZernikesToPsfWidth

from .. import BendModeToForce, OFCData, SensitivityMatrix


def make_quadrature_grid(
    rings: int,
    spokes: int,
    field_radius: float,
) -> tuple[list[tuple[float, float]], np.ndarray]:
    """Create a quadrature grid on a circular field.

    Parameters
    ----------
    rings : `int`
        Number of radial quadrature rings.
    spokes : `int`
        Number of azimuthal spokes.
    field_radius : `float`
        Field radius in degrees.

    Returns
    -------
    field_angles : `list` [`tuple` [`float`, `float`]]
        List of (x, y) field angles in degrees.
    field_weights : `np.ndarray`
        Quadrature weights for each field point, normalized to sum to 1.
    """
    li, w_ring = np.polynomial.legendre.leggauss(rings)
    radii = np.sqrt((1.0 + li) / 2.0) * field_radius
    w_ring = w_ring * np.pi / (2.0 * spokes)

    azs = np.linspace(0.0, 2.0 * np.pi, spokes, endpoint=False)
    radii, azs = np.meshgrid(radii, azs, indexing="ij")

    x = (radii * np.cos(azs)).ravel()
    y = (radii * np.sin(azs)).ravel()
    field_angles = [(float(xx), float(yy)) for xx, yy in zip(x, y)]

    field_weights = np.broadcast_to(w_ring[:, np.newaxis], radii.shape).ravel()
    field_weights = field_weights / np.sum(field_weights)

    return field_angles, field_weights


def compute_fwhm_matrix(
    ofc_data: OFCData,
    dz_sensitivity_matrix: SensitivityMatrix,
    field_angles: list,
) -> np.ndarray:
    """Compute the FWHM matrix in the legacy flattened format.

    Parameters
    ----------
    ofc_data : `OFCData`
        OFC data object.
    dz_sensitivity_matrix : `SensitivityMatrix`
        Double-Zernike sensitivity matrix object.
    field_angles : `list`
        Field angles at which to evaluate the matrix.

    Returns
    -------
    fwhm_matrix : `np.ndarray`
        FWHM matrix with shape (n_field * n_zernike, n_dof_used).
    """
    sensitivity_matrix = dz_sensitivity_matrix.evaluate(field_angles, rotation_angle=0.0)

    sensitivity_matrix = sensitivity_matrix[:, dz_sensitivity_matrix.ofc_data.zn_idx, :]

    fwhm_matrix = np.zeros(sensitivity_matrix.shape)
    for idy in range(sensitivity_matrix.shape[0]):
        fwhm_matrix[idy, ...] = convertZernikesToPsfWidth(sensitivity_matrix[idy, ...].T).T

    size = fwhm_matrix.shape[2]
    fwhm_matrix = fwhm_matrix.reshape((-1, size))
    fwhm_matrix = fwhm_matrix[..., ofc_data.dof_idx]

    return fwhm_matrix


def compute_fwhm_matrix_per_field(
    ofc_data: OFCData,
    dz_sensitivity_matrix: SensitivityMatrix,
    field_angles: list,
) -> np.ndarray:
    """Compute the FWHM response aggregated per field point.

    Parameters
    ----------
    ofc_data : `OFCData`
        OFC data object.
    dz_sensitivity_matrix : `SensitivityMatrix`
        Double-Zernike sensitivity matrix object.
    field_angles : `list`
        Field angles at which to evaluate the matrix.

    Returns
    -------
    fwhm_per_field : `np.ndarray`
        FWHM response per field point, with shape (n_field, n_dof_used).
    """
    sensitivity_matrix = dz_sensitivity_matrix.evaluate(field_angles, rotation_angle=0.0)

    sensitivity_matrix = sensitivity_matrix[:, dz_sensitivity_matrix.ofc_data.zn_idx, :]

    fwhm_matrix = np.zeros(sensitivity_matrix.shape)
    for idy in range(sensitivity_matrix.shape[0]):
        fwhm_matrix[idy, ...] = convertZernikesToPsfWidth(sensitivity_matrix[idy, ...].T).T

    fwhm_matrix = fwhm_matrix[..., ofc_data.dof_idx]
    fwhm_per_field = np.sqrt(np.sum(fwhm_matrix**2, axis=1))

    return fwhm_per_field


def compute_range_weights(ofc_data: OFCData) -> np.ndarray:
    """Compute range-based normalization factors.

    Parameters
    ----------
    ofc_data : `OFCData`
        OFC data object.

    Returns
    -------
    range_weights : `np.ndarray`
        Range-based weights for the used degrees of freedom.
    """
    m1m3_bending_range = ofc_data.m1m3_force_range / 20.0
    m2_bending_range = ofc_data.m2_force_range / 20.0

    m1m3_bmf = BendModeToForce("M1M3", ofc_data)
    m2_bmf = BendModeToForce("M2", ofc_data)

    range_weights_all = np.concatenate(
        (
            ofc_data.rb_stroke,
            m1m3_bending_range / np.max(np.abs(m1m3_bmf.rot_mat), axis=0),
            m2_bending_range / np.max(np.abs(m2_bmf.rot_mat), axis=0),
        )
    )

    return range_weights_all[ofc_data.dof_idx]


def compute_fwhm_weights_legacy(fwhm_matrix: np.ndarray) -> np.ndarray:
    """Compute legacy FWHM weights.

    Parameters
    ----------
    fwhm_matrix : `np.ndarray`
        FWHM matrix in flattened legacy format.

    Returns
    -------
    fwhm_weights : `np.ndarray`
        FWHM weights.
    """
    return np.sqrt(np.sum(np.square(fwhm_matrix), axis=0))


def compute_fwhm_weights_quadrature(
    fwhm_per_field: np.ndarray,
    field_weights: np.ndarray,
) -> np.ndarray:
    """Compute quadrature-weighted FWHM weights.

    Parameters
    ----------
    fwhm_per_field : `np.ndarray`
        FWHM response per field point, shape (n_field, n_dof_used).
    field_weights : `np.ndarray`
        Normalized field weights, shape (n_field,).

    Returns
    -------
    fwhm_weights : `np.ndarray`
        Weighted FWHM weights.
    """
    return np.sqrt(np.sum(field_weights[:, None] * fwhm_per_field**2, axis=0))


def compute_normalization_weights(
    range_weights: np.ndarray,
    fwhm_weights: np.ndarray,
    range_exponent: float = 1.0,
    fwhm_exponent: float = 1.0,
) -> np.ndarray:
    """Combine range and FWHM weights with configurable exponents.

    Parameters
    ----------
    range_weights : `np.ndarray`
        Range-based weights.
    fwhm_weights : `np.ndarray`
        FWHM-based weights.
    range_exponent : `float`, optional
        Exponent applied to the range-based weights.
    fwhm_exponent : `float`, optional
        Exponent applied to the FWHM-based weights.

    Returns
    -------
    normalization_weights : `np.ndarray`
        Final normalization weights.
    """
    return (range_weights**range_exponent) * (fwhm_weights**fwhm_exponent)


def save_normalization_weights(
    normalization_weights: np.ndarray,
    output_dir: str,
    metadata: dict,
) -> None:
    """Save the normalization weights.

    Parameters
    ----------
    normalization_weights : `np.ndarray`
        Normalization weights.
    output_dir : `str`
        Output directory to save the normalization weights.
    metadata : `dict`
        Metadata describing how the weights were generated.
    """
    yaml_file_path = Path(output_dir) / "normalization_weights.yaml"

    payload = {
        "metadata": metadata,
        "normalization_weights": normalization_weights.tolist(),
    }

    with open(yaml_file_path, "w") as yaml_file:
        header = (
            "---\n"
            "# Normalization weights for the degrees of freedom\n"
            "#\n"
            "# These weights are used to normalize the sensitivity matrix.\n"
            "# They combine a range-based factor r_i and an FWHM-based factor f_i\n"
            "# according to\n"
            "#\n"
            "#   w_i = r_i^alpha * f_i^beta\n"
            "#\n"
            "# where alpha is the range exponent and beta is the FWHM exponent.\n"
            "#\n"
            "# The quadrature option computes the field-averaged FWHM response using\n"
            "# a circular quadrature grid over the field of view.\n"
            "\n"
        )
        yaml_file.write(header)
        yaml.safe_dump(payload, yaml_file, sort_keys=False)


def generate_normalization_weights() -> None:
    """Generate normalization weights for the sensitivity matrix."""
    args = parse_arguments()

    ofc_data = OFCData(args.instrument)
    dz_sensitivity_matrix = SensitivityMatrix(ofc_data)

    range_weights = compute_range_weights(ofc_data)

    if args.method == "legacy":
        sensor_name_list = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]
        field_angles = [ofc_data.sample_points[sensor] for sensor in sensor_name_list]

        fwhm_matrix = compute_fwhm_matrix(ofc_data, dz_sensitivity_matrix, field_angles)
        fwhm_weights = compute_fwhm_weights_legacy(fwhm_matrix)

        metadata = {
            "instrument": args.instrument,
            "method": "legacy",
            "field_angles": field_angles,
            "range_exponent": args.range_exponent,
            "fwhm_exponent": args.fwhm_exponent,
        }

    else:
        field_angles, field_weights = make_quadrature_grid(
            rings=args.rings,
            spokes=args.spokes,
            field_radius=args.field_radius,
        )

        fwhm_per_field = compute_fwhm_matrix_per_field(ofc_data, dz_sensitivity_matrix, field_angles)
        fwhm_weights = compute_fwhm_weights_quadrature(fwhm_per_field, field_weights)

        metadata = {
            "instrument": args.instrument,
            "method": "quadrature",
            "rings": args.rings,
            "spokes": args.spokes,
            "field_radius": args.field_radius,
            "range_exponent": args.range_exponent,
            "fwhm_exponent": args.fwhm_exponent,
        }

    normalization_weights = compute_normalization_weights(
        range_weights=range_weights,
        fwhm_weights=fwhm_weights,
        range_exponent=args.range_exponent,
        fwhm_exponent=args.fwhm_exponent,
    )

    save_normalization_weights(normalization_weights, args.output_dir, metadata)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate normalization weights for the OFC sensitivity matrix."
    )

    parser.add_argument(
        "output_dir",
        help="Output path where normalization weights should be stored",
    )

    parser.add_argument(
        "--instrument",
        choices=["lsst", "comcam"],
        default="lsst",
        help="Type of instrument to use",
    )

    parser.add_argument(
        "--method",
        choices=["legacy", "quadrature"],
        default="legacy",
        help="Method used to compute FWHM weights",
    )

    parser.add_argument(
        "--range-exponent",
        type=float,
        default=1.0,
        help="Exponent applied to the range-based weights",
    )

    parser.add_argument(
        "--fwhm-exponent",
        type=float,
        default=1.0,
        help="Exponent applied to the FWHM-based weights",
    )

    parser.add_argument(
        "--rings",
        type=int,
        default=5,
        help="Number of radial rings for the quadrature method",
    )

    parser.add_argument(
        "--spokes",
        type=int,
        default=6,
        help="Number of azimuthal spokes for the quadrature method",
    )

    parser.add_argument(
        "--field-radius",
        type=float,
        default=1.75,
        help="Field radius in degrees for the quadrature method",
    )

    return parser.parse_args()
