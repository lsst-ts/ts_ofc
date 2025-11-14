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
import pathlib

import batoid
import galsim
import numpy as np
import yaml
from lsst.ts.imsim import OpdMetrology
from lsst.ts.ofc import OFCData
from tqdm import tqdm


def save_alpha_values(alpha_values: np.ndarray, path: str) -> None:
    """Save alpha values to a yaml file.

    Parameters
    ----------
    alpha_values : np.ndarray
        Alpha values for the normalized point-source sensitivity.
    path : str
        Path to save the alpha values.
    """

    # Convert numpy array to a list,
    # as yaml.dump cannot handle numpy arrays directly
    alpha_values_list = alpha_values.tolist()

    # Complete path to the yaml file
    yaml_file_path = f"{path}/alpha_values.yaml"

    # Write header and alpha values to the yaml file
    with open(yaml_file_path, "w") as yaml_file:
        header = (
            "---\n"
            "\n# Default alpha coefficient for the normalized point-source sensitivity\n"
            "# There are 25 terms of alpha value here for z4-z28 to use.\n"
            "# Alpha values are shown in um^{-2} and they come from fitting\n"
            "# PSSN ~ 1 - alpha * delta^2\n"
            "# Eq (7.1) in Normalized Point Source Sensitivity for LSST\n"
            "# The procedure to obtain them is detailed in scripts/generate_alpha_values.py\n"
            "# For more details, please check the page 19-21 in:\n"
            "# https://docushare.lsst.org/docushare/dsweb/Get/Document-18041/150513.pptx.pdf\n\n"
        )
        yaml_file.write(header)
        yaml.dump(alpha_values_list, yaml_file)


def get_alpha_values(
    config: dict,
    instrument: str,
    band: str,
    znmin: int = 4,
    znmax: int = 28,
) -> np.ndarray:
    """Calculate alpha values for the normalized point-source sensitivity.

    Parameters
    ----------
    config : dict
        Configuration dictionary.
    instrument : str
        Instrument name either 'LSST' or 'ComCam'
    band : str
        Filter band.
    znmin : int
        Minimum Zernike index.
    znmax : int
        Maximum Zernike index.

    Returns
    -------
    np.ndarray
        Alpha values for the normalized point-source sensitivity.

    Raises
    ------
    ValueError
        If znmax is smaller than znmin.
    ValueError
        If negative weights are found in the Gaussian Quadrature points.
    """

    # If znmax is smaller than znmin, raise an error
    if znmax < znmin:
        raise ValueError("znmax should be larger than znmin")

    # Set wavelength and number of zernikes used
    num_zk = znmax - znmin + 1
    wavelength = config["wavelengths"][band]

    # Set the increments of zernikes used to do the fit
    # These increments are selected to be 2,4,6,8,10 for historical reasons.
    # They correspond to the ones used in
    # https://docushare.lsst.org/docushare/dsweb/Get/Document-18041/150513.pptx.pdf
    # Other increments could be used, as long as the final RMS of the fit
    # is smaller than 1e-4
    increments = np.array([2, 4, 6, 8, 10]) * wavelength * 1e-2

    # Create OFCData, OPDMetrology and fiducial telescope
    ofc_data = OFCData("lsst")
    opd_metrology = OpdMetrology()

    if band == "ref":
        fiducial = batoid.Optic.fromYaml(f"{instrument.upper()}_g_500.yaml")
    else:
        fiducial = batoid.Optic.fromYaml(f"{instrument.upper()}_{band}.yaml")

    # Get the field angles of the gaussian quadrature points
    field_angles = [ofc_data.gq_points[sensor] for sensor in range(len(ofc_data.gq_weights))]
    field_x, field_y = zip(*field_angles)

    # Load the gaussian quadrature weights
    imqw = [ofc_data.gq_weights[sensor] for sensor in range(len(ofc_data.gq_weights))]
    # Check if any weight is negative and raise an error
    if any(weight < 0 for weight in imqw):
        raise ValueError("Negative weights found in the Gaussian Quadrature points")
    n_imqw = imqw / np.sum(imqw)

    # Create empty arrays to store the pssn values
    pssn_avg = np.zeros((num_zk, len(increments)))
    pssn_gq_points = np.zeros((num_zk, len(field_angles), len(increments)))
    alpha_values = np.zeros(num_zk)

    for id_zk in tqdm(range(num_zk)):
        zk = np.zeros(25)

        # For each increment, compute the PSSN values
        for id_increment, increment in enumerate(increments):
            # Set value of zernike perturbation
            zk[id_zk] = increment

            for id_angle in range(len(field_angles)):
                # Convert field angles to radians
                field_x = np.deg2rad(field_angles[id_angle][0])
                field_y = np.deg2rad(field_angles[id_angle][1])

                # Calculate the wavefront without perturbation
                # to retrieve the opd mask
                # nx = 255 is the size of the grid to use (255x255)
                opd_w = batoid.wavefront(fiducial, field_x, field_y, wavelength=wavelength, nx=255)
                opd_size = opd_w.array.shape[0]
                opd_grid_1d = np.linspace(-1, 1, opd_size)
                opd_x, opd_y = np.meshgrid(opd_grid_1d, opd_grid_1d)
                non_masked = ~opd_w.array.mask

                # Set zernikes for the new opd
                new_opd = opd_w.array.copy()
                new_opd[non_masked] = galsim.zernike.Zernike(
                    np.concatenate([np.zeros(znmin), zk]),
                    R_inner=config["pupil"]["radius_inner"] / config["pupil"]["radius_outer"],
                )(opd_x[non_masked], opd_y[non_masked])

                # Calculate PSSN from the new opd
                pssn = opd_metrology.calc_pssn(wavelength, opd_map=new_opd)

                # Store pssn values
                pssn_gq_points[id_zk, id_angle, id_increment] = pssn

            # Calculate the average PSSN value
            # among all the gaussian quadrature points
            pssn_avg[id_zk, id_increment] = np.sum(n_imqw * pssn_gq_points[id_zk, :, id_increment])

        # Make the linear fit for 1 - PSSN = alpha * delta^2
        # where delta is the zernike increment in um
        true_values = 1 - pssn_avg[id_zk, :]
        # Fit a line to the data
        alpha, b = np.polyfit(increments[:-1] ** 2, true_values[:-1], 1)
        predicted_values = alpha * increments**2 + b

        # Calculate the RMS of the fit
        rms = np.sqrt(np.mean((true_values - predicted_values) ** 2))

        # If rms is larger than 1e-3, print a warning
        if rms > 1e-3:
            print(f"Warning: RMS of the fit is larger than 1e-3 for Z{id_zk + 4}")

        # Store the alpha value
        alpha_values[id_zk] = alpha

    return alpha_values


def main(args: argparse.Namespace) -> None:
    """Generate Intrinsic Double Zernike files
    based on batoid simulation package

    Parameters
    ----------
    args : argparse.Namespace
        Arguments passed from command line.

    Raises
    ------
    RuntimeError
        If the configuration file for the specified instrument is not found.
    """

    # Load configuration file
    config_dir = pathlib.Path(__file__).resolve().parents[5] / "policy"

    try:
        with open(config_dir / "configurations" / "lsst.yaml") as fp:
            config = yaml.safe_load(fp)
    except FileNotFoundError:
        raise RuntimeError(f"Configuration file for {args.instrument} not found in {config_dir}")

    # Compute intrinsic zernikes
    alpha_values = get_alpha_values(
        config,
        "lsst",
        args.filter,
        znmin=args.znmin,
        znmax=args.znmax,
    )

    # Save the intrinsic double zernikes
    save_alpha_values(alpha_values, args.path)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Intrinsic Double Zernike files based on batoid simulation package"
    )

    parser.add_argument(
        "path",
        default=None,
        help="Path where intrinsic zernikes should be stored",
    )

    parser.add_argument(
        "--filter",
        choices=["ref", "r", "i", "z", "y", "g", "u"],
        help="What filter to generate the double zernikes for",
    )

    parser.add_argument(
        "--znmin",
        default=4,
        type=int,
        help="Minimum zk index",
    )

    parser.add_argument(
        "--znmax",
        default=28,
        type=int,
        help="Maximum zk index",
    )

    return parser.parse_args()


def generate_alpha_values() -> None:
    """Generate alpha values for the normalized point-source sensitivity."""
    main(parse_arguments())


if __name__ == "__main__":
    main(parse_arguments())
