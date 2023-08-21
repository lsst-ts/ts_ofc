import argparse
from astropy.io import fits
import batoid
import batoid_rubin
import galsim
import numpy as np
import ruamel.yaml
from tqdm import tqdm

import textwrap
from typing import Tuple
import pathlib

def get_fiducial(instrument, band) -> Tuple[batoid.Optic, float]:
    fiducial = batoid.Optic.fromYaml(f"{instrument}_{band}.yaml")

    wavelength = {
        "u": 0.365,
        "g": 0.480,
        "r": 0.622,
        "i": 0.754,
        "z": 0.869,
        "y": 0.971,
    }[band]

    return fiducial, wavelength

def double_zernike(
    optic, field, wavelength, rings=7, spokes=25, jmax=22, kmax=22, **kwargs
) -> np.ndarray:
    if spokes is None:
        spokes = 2 * rings + 1

    Li, w = np.polynomial.legendre.leggauss(rings)
    radii = np.sqrt((1 + Li) / 2) * field
    w *= np.pi / (2 * spokes)
    azs = np.linspace(0, 2 * np.pi, spokes, endpoint=False)
    radii, azs = np.meshgrid(radii, azs)
    w = np.broadcast_to(w, radii.shape)
    radii = radii.ravel()
    azs = azs.ravel()
    w = w.ravel()
    thx = radii * np.cos(azs)
    thy = radii * np.sin(azs)
    coefs = []
    for thx_, thy_ in zip(thx, thy):
        coefs.append(
            batoid.zernike(optic, thx_, thy_, wavelength, jmax=jmax, eps=0.61, nx=255)
        )
    coefs = np.array(coefs)

    basis = galsim.zernike.zernikeBasis(kmax, thx, thy, R_outer=field)
    dzs = np.dot(basis, coefs * w[:, None]) / np.pi

    return dzs

def get_dz0(config, instrument, band, jmax=22, kmax=15):
    fiducial, wavelength = get_fiducial(instrument, band)

    return double_zernike(
        fiducial,
        field=np.deg2rad(config['pupil']['R_outer']),
        wavelength=wavelength*1e-6,  # nm -> m
        eps=0.61,
        jmax=jmax,
        kmax=kmax
    )

def get_sensitivity_dz(config, instrument, band, ndof=50, jmax=22, kmax=30):
    A = np.empty((ndof, kmax+1, jmax+1))
    fiducial, wavelength = get_fiducial(instrument, band)
    swap = [2, 5, 8, 10, 13, 15, 16, 18, 20]
    dz0 = get_dz0(config, instrument, band, jmax, kmax)
    dz0[:, swap] *= -1
    for idof in tqdm(range(ndof)):
        applied_dof = np.zeros(50)
        applied_dof[idof] = 1
        fiducial, wavelength = get_fiducial(instrument, band)
        builder = batoid_rubin.LSSTBuilder(fiducial).with_aos_dof(applied_dof)
        telescope = builder.build()

        dz1 = double_zernike(
            telescope,
            field=np.deg2rad(config['pupil']['R_outer']),
            wavelength=wavelength*1e-6,
            eps=0.61,
            jmax=jmax,
            kmax=kmax,
        )
    
        dz1[:, swap] *= -1
        A[idof] = (dz1-dz0)/1
    
    A = np.einsum('ijk->jki', A)

    return A*wavelength

def main(args: argparse.Namespace):
    # Load configuration
    config_dir = pathlib.Path(__file__).resolve().parents[5] / "policy"
    with open( config_dir / 'configurations' / f"{args.instrument.lower()}.yaml") as fp:
        import yaml
        config = yaml.safe_load(fp)

    sensitivity_matrix = get_sensitivity_dz(config, args.instrument, args.filter)

    with open(f"{args.path}/{args.instrument.lower()}_{args.filter}_sensitivity_dz_31_23_50.yaml", "w") as yaml_file:
        yaml_file.write(
            f"--- \n \
            \n # Sensitivity matrix for the r band. \
            \n # Dimensions: (31,23,50) \
            \n # The first dimension is kmax = 31, corresponds to number of Zernike \
            \n # polynomials used to measure wavefront variation accross the pupil. \
            \n # The second dimension is jmax = 23, corresponds to number of Zernike \
            \n # polynomials used to measure wavefront variation accross the field. \
            \n # The third dimension is 50 degree of freedom (DOF) \
            \n # polynomials used to measure wavefront variation accross the field. \
            \n # The DOF are (1) M2 dz, dx, dy in um, (2) M2 rx, ry in arcsec, \
            \n # (3) Cam dz, dx, dy in um, (4) Cam rx, ry in arcsec, (5) 20 M1M3 bending mode in um,  \
            \n # (6) 20 M2 bending mode in um. \
            \n # (6) Units are um (Zk) / um or arcsec (dof). \
            \n \n"
        )

        yaml = ruamel.yaml.YAML()
        yaml.indent(offset=2)
        yaml.width = 80

        for sublist in sensitivity_matrix.tolist():
            yaml_file.write('- ')
            for idx, subsublist in enumerate(sublist):
                if idx != 0:
                    yaml_file.write('  ')
                formatted_sublist = textwrap.fill(
                    "- [" + ", ".join(map(str, subsublist)), width=100, subsequent_indent="  "
                )
                yaml_file.write(formatted_sublist + "] \n")

    prihdr = fits.Header()
    prihdr['Content'] = 'Sensitivity matrix (k, j, dof)'
    prihdr['Dim'] = '(31,23,50)'
    hdu = fits.PrimaryHDU(sensitivity_matrix, header=prihdr)
    hdu.writeto(f"{args.path}/{args.instrument.lower()}_sensitivity_dz_31_23_50.fits", overwrite=True)

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Double Zernike Sensitivity Matrix based on batoid simulation package"
    )

    parser.add_argument(
        "path",
        default=None, 
        help="Path where sensitivity matrix should be stored",
    )

    parser.add_argument(
        "filter",
        choices=["r", "i", "z", "y", "g", "u"],
        help="What filter to generate the sensitivity matrix for",
    )

    parser.add_argument(
        "--instrument", choices=["LSST", "ComCam"], default='LSST', help="Type of instrument to use", 
    )

    return parser.parse_args()

if __name__ == "__main__":
    main(parse_arguments())
