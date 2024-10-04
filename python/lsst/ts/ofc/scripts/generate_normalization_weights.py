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

import numpy as np
import yaml
from lsst.ts.wep.utils import convertZernikesToPsfWidth

from .. import BendModeToForce, OFCData, SensitivityMatrix


def compute_fwhm_matrix(
    ofc_data: OFCData, dz_sensitivity_matrix: SensitivityMatrix, field_angles: list
) -> np.ndarray:
    # Evaluate sensitivity matrix at sensor positions
    sensitivity_matrix = dz_sensitivity_matrix.evaluate(
        field_angles, rotation_angle=0.0
    )

    # Select sensitivity matrix only at used zernikes
    sensitivity_matrix = sensitivity_matrix[:, dz_sensitivity_matrix.ofc_data.zn_idx, :]

    fwhm_matrix = np.zeros(sensitivity_matrix.shape)
    for idy in range(sensitivity_matrix.shape[0]):
        fwhm_matrix[idy, ...] = convertZernikesToPsfWidth(
            sensitivity_matrix[idy, ...].T
        ).T

    size = fwhm_matrix.shape[2]
    fwhm_matrix = fwhm_matrix.reshape((-1, size))

    # Select sensitivity matrix only at used degrees of freedom
    fwhm_matrix = fwhm_matrix[..., ofc_data.dof_idx]

    return fwhm_matrix


def compute_normalization_weights(
    ofc_data: OFCData, fwhm_matrix: np.ndarray
) -> np.ndarray:
    """Compute the normalization weights.

    Parameters
    ----------
    fwhm_matrix : np.ndarray
        FWHM matrix.

    Returns
    -------
    np.ndarray
        Normalization weights.
    """
    m1m3_bending_range = ofc_data.m1m3_force_range / 20
    m2_bending_range = ofc_data.m2_force_range / 20

    m1m3_bmf = BendModeToForce("M1M3", ofc_data)
    m2_bmf = BendModeToForce("M2", ofc_data)

    range_weights = np.concatenate(
        (
            ofc_data.rb_stroke,
            m1m3_bending_range / np.max(np.abs(m1m3_bmf.rot_mat), axis=0),
            m2_bending_range / np.max(np.abs(m2_bmf.rot_mat), axis=0),
        )
    )

    fwhm_weights = np.zeros(50)
    for i in range(50):
        fwhm_weights[i] = np.sqrt(np.sum(np.square(fwhm_matrix[:, i])))

    normalization_weights = range_weights * fwhm_weights

    return normalization_weights


def save_normalization_weights(
    normalization_weights: np.ndarray, output_dir: str
) -> None:
    """Save the normalization weights.

    Parameters
    ----------
    normalization_weights : np.ndarray
        Normalization weights.
    output_dir : str
        Output directory to save the normalization weights.
    """
    yaml_file_path = f"{output_dir}/normalization_weights.yaml"

    with open(yaml_file_path, "w") as yaml_file:
        header = """
            ---
            # Normalization weights for the degrees of freedom
            # Description: Normalization weights for the sensitivity matrix
            #
            # The normalization weights are used to normalize
            # the sensitivity matrix and be able to operate in
            # a different basis. The normalization weights are
            # effectively a rescaling diagonal matix that is
            # applied to the sensitivity to equalize the relevance
            # of the different degrees of freedom (namelly, the
            # different units and ranges of the degrees of freedom).
            # The default is simply an identity (weights = 1)),
            # which means that the sensitivity matrix is not
            # normalized in any way. Units can be dimensionless.
            # The reduced basis weights units are um of range * arcsec of FWHM.
            # But the matrix is denormalized before retrieving the optical state,
            # so it should not be relevant.\n
            """
        yaml_file.write(header)
        yaml.dump(normalization_weights.tolist(), yaml_file)


def generate_normalization_weights() -> None:
    """Generate normalization weights for the sensitivity matrix."""
    args = parse_arguments()

    ofc_data = OFCData(args.instrument)

    sensor_name_list = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]
    field_angles = [ofc_data.sample_points[sensor] for sensor in sensor_name_list]

    dz_sensitivity_matrix = SensitivityMatrix(ofc_data)

    fwhm_matrix = compute_fwhm_matrix(ofc_data, dz_sensitivity_matrix, field_angles)

    normalization_weights = compute_normalization_weights(ofc_data, fwhm_matrix)

    save_normalization_weights(normalization_weights, args.output_dir)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Double Zernike Sensitivity Matrix based on batoid simulation package"
    )

    parser.add_argument(
        "output_dir",
        default=None,
        help="Output path where sensitivity matrix should be stored",
    )

    parser.add_argument(
        "--instrument",
        choices=["lsst", "comcam"],
        default="lsst",
        help="Type of instrument to use",
    )

    return parser.parse_args()
