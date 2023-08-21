import argparse
from astropy.io import fits
import batoid
import galsim
import numpy as np
import ruamel.yaml

import textwrap
from typing import Tuple
import pathlib
from generate_sensitivity_matrix import get_fiducial, double_zernike


def get_intrinsic_zk(config, instrument, band, jmax=22, kmax=15) -> np.ndarray:
    fiducial, wavelength = get_fiducial(instrument, band)

    return (
        double_zernike(
            fiducial,
            field=np.deg2rad(config['pupil']['R_outer']),
            wavelength=wavelength * 1e-6,  # nm -> m
            eps=0.61,
            jmax=jmax,
            kmax=kmax,
        )
    )

def save_intrinsic_zk(filter_name, intrinsic_zk, path):
    with open(f"{path}/intrinsic_zk_{filter_name}_31_23.yaml", "w") as yaml_file:
        yaml_file.write(
            f"--- \n \
            \n # Intrinsic Zk for the {filter_name} band. \
            \n # The first dimension is kmax = 31, corresponds to number of Zernike \
            \n # polynomials used to measure wavefront variation accross the pupil. \
            \n # The second dimension is jmax = 23, corresponds to number of Zernike \
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

    prihdr = fits.Header()
    prihdr["Content"] = "Intrinsic zernikes (k, j)"
    prihdr["Dim"] = "(31,23)"
    hdu = fits.PrimaryHDU(intrinsic, header=prihdr)
    hdu.writeto(f"{path}/intrinsic_zk_{filter_name}_31_23.fits", overwrite=True)

def main(args: argparse.Namespace):
    # Load configuration
    config_dir = pathlib.Path(__file__).resolve().parents[5] / "policy"
    with open( config_dir / 'configurations' / f"{args.instrument.lower()}.yaml") as fp:
        import yaml
        config = yaml.safe_load(fp)

    intrinsic = get_intrinsic_zk(config, args.instrument, args.filter, jmax=22, kmax=30)
    swap = [2, 5, 8, 10, 13, 15, 16, 18, 20]
    intrinsic[:, swap] *= -1

    save_intrinsic_zk(args.filter, intrinsic, args.path)

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
        "--instrument", choices=["LSST", "ComCam"], default='LSST', help="Type of instrument to use", 
    )

    return parser.parse_args()

if __name__ == "__main__":
    main(parse_arguments())
