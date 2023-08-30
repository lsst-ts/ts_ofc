import argparse
from astropy.io import fits
import numpy as np
import ruamel.yaml

import textwrap
import pathlib
from generate_sensitivity_matrix import get_intrinsic_zk


def save_intrinsic_zk(
    filter_name: str,
    intrinsic_zk: np.ndarray,
    path: str,
    kmax: int,
) -> None:
    """Save intrinsic zernike coefficients to a fits file and a yaml file.

    Parameters
    ----------
    filter_name : str
        Name of the filter. Either 'u', 'g', 'r', 'i', 'z', or 'y'.
    intrinsic_zk : np.ndarray
        Intrinsic zernike coefficients.
    path : str
        Path to save the intrinsic zernike coefficients.
    kmax : int
        Maximum zernike index for the zernikes across the pupil
    """

    # Save yaml file with header and content shown as legacy yaml files.
    with open(
        f"{path}/intrinsic_zk_{filter_name}_{kmax + 1}_23.yaml", "w"
    ) as yaml_file:
        yaml_file.write(
            f"--- \n \
            \n # Intrinsic Zk for the {filter_name} band. \
            \n # The first dimension is kmax = 31, corresponds to number of Zernike \
            \n # polynomials used to measure wavefront variation accross the pupil. \
            \n # The second dimension is 23, the first element in that dimension is meaningless \
            \n # the other 22 elements, are jmax = 22 which corresponds to number of Zernike \
            \n # polynomials used to measure wavefront variation accross the field. \
            \n # Units are (Zk in um)/ (wavelength in um) \
            \n \n"
        )

        yaml = ruamel.yaml.YAML()
        yaml.indent(offset=2)
        yaml.width = 80

        for sublist in intrinsic_zk.tolist():
            formatted_sublist = textwrap.fill(
                "- [" + ", ".join(map(str, sublist)), width=100, subsequent_indent="  "
            )
            yaml_file.write(formatted_sublist + "] \n")

    # Save fits file
    prihdr = fits.Header()
    prihdr["Content"] = "Intrinsic zernikes (k, j)"
    prihdr["Dim"] = "(31,23)"
    hdu = fits.PrimaryHDU(intrinsic_zk, header=prihdr)
    hdu.writeto(f"{path}/intrinsic_zk_{filter_name}_31_23.fits", overwrite=True)


def main(args: argparse.Namespace) -> None:
    """Generate Intrinsic Double Zernike files
    based on batoid simulation package

    Parameters
    ----------
    args : argparse.Namespace
        Arguments passed from command line.

    """

    # Load configuration file
    config_dir = pathlib.Path(__file__).resolve().parents[5] / "policy"
    with open(config_dir / "configurations" / f"{args.instrument.lower()}.yaml") as fp:
        import yaml

        config = yaml.safe_load(fp)

    # Compute intrinsic zernikes
    intrinsic = get_intrinsic_zk(
        config, args.instrument, args.filter, jmax=22, kmax=args.kmax, rings=15, spokes=55
    )

    # Swap corresponding zernike that are flipped in batoid
    swap = [2, 5, 8, 10, 13, 15, 16, 18, 20]
    intrinsic[:, swap] *= -1

    # Save the intrinsic double zernikes
    save_intrinsic_zk(args.filter, intrinsic, args.path, kmax=kmax)


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
        "filter",
        choices=["r", "i", "z", "y", "g", "u"],
        help="What filter to generate the double zernikes for",
    )

    parser.add_argument(
        "--instrument",
        choices=["LSST", "ComCam"],
        default="LSST",
        help="Type of instrument to use",
    )

    parser.add_argument(
        "--kmax",
        default=30,
        type=int,
        help="Maximum kmax index",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main(parse_arguments())
