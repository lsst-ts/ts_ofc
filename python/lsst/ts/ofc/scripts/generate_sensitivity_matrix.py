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


def get_fiducial(
    instrument: str,
    band: str,
) -> Tuple[batoid.Optic, float]:
    """Get fiducial optical system and wavelength
    for a given instrument and band.

    Parameters
    ----------
    instrument : str
        Name of the instrument. Either 'LSST' or 'ComCam'.
    band : str
        Name of the filter. Either 'u', 'g', 'r', 'i', 'z', or 'y'.

    Returns
    -------
    fiducial : batoid.Optic
        Fiducial optical system.
    wavelength : float
        Wavelength in um.
    """

    # Get fiducial optical system from batoid.
    fiducial = batoid.Optic.fromYaml(f"{instrument}_{band}.yaml")

    # Get corresponding filter wavelength in um.
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
    optic: batoid.Optic,
    field: float,
    wavelength: float,
    rings: int = 11,
    spokes: int = 35,
    jmax: int = 22,
    kmax: int = 22,
    **kwargs,
) -> np.ndarray:
    """Compute Double Zernike coefficients for a given optical system.

    Parameters
    ----------
    optic : batoid.Optic
        Optical system.
    field : float
        Field angle in radians.
    wavelength : float
        Wavelength in um.
    rings : int, optional
        Number of rings in the field, by default 7
    spokes : int, optional
        Number of spokes in each ring, by default 25
    jmax : int, optional
        Maximum j index, by default 22
    kmax : int, optional
        Maximum k index, by default 22

    Returns
    -------
    np.ndarray
        Double Zernike coefficients.

    Notes
    -----
    This function is adapted from the batoid.doubleZernike function in batoid.
    """

    if spokes is None:
        spokes = 2 * rings + 1

    # Generate points
    Li, w = np.polynomial.legendre.leggauss(rings)
    radii = np.sqrt((1 + Li) / 2) * field
    w *= np.pi / (2 * spokes)
    azs = np.linspace(0, 2 * np.pi, spokes, endpoint=False)
    radii, azs = np.meshgrid(radii, azs)
    w = np.broadcast_to(w, radii.shape)
    radii = radii.ravel()
    azs = azs.ravel()
    w = w.ravel()

    # Convert to angles
    thx = radii * np.cos(azs)
    thy = radii * np.sin(azs)

    # Compute Zernike coefficients
    coefs = []
    for thx_, thy_ in zip(thx, thy):
        coefs.append(
            batoid.zernike(optic, thx_, thy_, wavelength, jmax=jmax, eps=0.61, nx=255)
        )
    coefs = np.array(coefs)

    basis = galsim.zernike.zernikeBasis(kmax, thx, thy, R_outer=field)
    dzs = np.dot(basis, coefs * w[:, None]) / np.pi

    return dzs


def get_intrinsic_zk(
    config: dict,
    instrument: str,
    band: str,
    jmax: int = 22,
    kmax: int = 15,
    rings: int = 11,
    spokes: int = 35,
) -> np.ndarray:
    """Get the intrinsic double zernike coefficients
    for a given instrument and band.

    Parameters
    ----------
    config : dict
        Configuration dictionary.
    instrument : str
        Name of the instrument. Either 'LSST' or 'ComCam'.
    band : str
        Name of the filter. Either 'u', 'g', 'r', 'i', 'z', or 'y'.
    jmax : int, optional
        Maximum j index, by default 22
    kmax : int, optional
        Maximum k index, by default 15
    rings : int, optional
        Number of rings in the field, by default 11
    spokes : int, optional
        Number of spokes in each ring, by default 35

    Returns
    -------
    dz0 : np.ndarray
        Intrinsic double zernike coefficients.
    """

    fiducial, wavelength = get_fiducial(instrument, band)

    return double_zernike(
        fiducial,
        field=np.deg2rad(config["pupil"]["R_outer"]),
        wavelength=wavelength * 1e-6,  # nm -> m
        eps=0.61,
        rings=rings,
        spokes=spokes,
        jmax=jmax,
        kmax=kmax,
    )


def get_sensitivity_dz(
    config: dict,
    instrument: str,
    band: str,
    ndof: int = 50,
    jmax: int = 22,
    kmax: int = 30,
) -> np.ndarray:
    """Get the double zernike sensitivity matrix
    for a given instrument and band.

    Parameters
    ----------
    config : dict
        Configuration dictionary.
    instrument : str
        Name of the instrument. Either 'LSST' or 'ComCam'.
    band : str
        Name of the filter. Either 'u', 'g', 'r', 'i', 'z', or 'y'.
    ndof : int, optional
        Number of degrees of freedom, by default 50
    jmax : int, optional
        Maximum j index, by default 22
    kmax: int, optional
        Maximum k index, by default 30

    Returns
    ----------
    sensitivity_matrix : np.ndarray
        Double zernike sensitivity matrix.
    """

    sensitivity_matrix = np.empty((ndof, kmax + 1, jmax + 1))
    # Get fiducial telescope
    fiducial, wavelength = get_fiducial(instrument, band)

    # Compute the intrinsic double zernike coefficients
    dz0 = get_intrinsic_zk(config, instrument, band, jmax, kmax)

    # Swap the zernikes that are flipped in batoid
    swap = [2, 5, 8, 10, 13, 15, 16, 18, 20]
    dz0[:, swap] *= -1

    # For each dof, compute the sensitivity matrix
    for idof in tqdm(range(ndof)):
        # Define degrees of freedom perturbation
        applied_dof = np.zeros(50)
        applied_dof[idof] = 1

        # Get fiducial telescope and apply degrees of freedom
        fiducial, wavelength = get_fiducial(instrument, band)
        builder = batoid_rubin.LSSTBuilder(fiducial).with_aos_dof(applied_dof)
        telescope = builder.build()

        # Compute the double zernikes with the given perturbation
        dz1 = double_zernike(
            telescope,
            field=np.deg2rad(config["pupil"]["R_outer"]),
            wavelength=wavelength * 1e-6,
            eps=0.61,
            jmax=jmax,
            kmax=kmax,
        )

        # Swap the zernikes that are flipped in batoid
        dz1[:, swap] *= -1

        # Compute the sensitivity matrix by subtracting the
        # intrinisc from the perturbed double zernikes
        sensitivity_matrix[idof] = (dz1 - dz0) / applied_dof[idof]

    # Reorder the indices so that it will be (jmax, kmax, ndof)
    sensitivity_matrix = np.einsum("ijk->jki", sensitivity_matrix)

    # Multiply by the wavlength
    sensitivity_matrix *= wavelength

    return sensitivity_matrix


def save_sensitivity_matrix(
    path: str, instrument: str, sensitivity_matrix: np.ndarray
) -> None:
    """Save intrinsic zernike coefficients to a fits file and a yaml file.

    Parameters
    ----------
    path : str
        Path to save the intrinsic zernike coefficients.
    instrument : str
        Name of the instrument. Either 'LSST' or 'ComCam'.
    sensitivity_matrix : np.ndarray
       Double Zernike coefficients for the sensitivity matrix.
    """

    # Save yaml file with header and content shown as legacy yaml files.
    with open(
        f"{path}/{instrument.lower()}_sensitivity_dz_31_23_50.yaml", "w"
    ) as yaml_file:
        yaml_file.write(
            "--- \n \
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
            yaml_file.write("- ")
            for idx, subsublist in enumerate(sublist):
                if idx != 0:
                    yaml_file.write("  ")
                formatted_sublist = textwrap.fill(
                    "- [" + ", ".join(map(str, subsublist)),
                    width=100,
                    subsequent_indent="  ",
                )
                yaml_file.write(formatted_sublist + "] \n")

    # Save fits file
    prihdr = fits.Header()
    prihdr["Content"] = "Sensitivity matrix (k, j, dof)"
    prihdr["Dim"] = "(31,23,50)"
    hdu = fits.PrimaryHDU(sensitivity_matrix, header=prihdr)
    hdu.writeto(
        f"{path}/{instrument.lower()}_sensitivity_dz_31_23_50.fits", overwrite=True
    )


def main(args: argparse.Namespace) -> None:
    """Generate and save double_Zernikes
        sensitivity matrix for a given instrument and band.

    Parameters
    ----------
    args : argparse.Namespace
        Command line arguments.
    """

    # Load configuration
    config_dir = pathlib.Path(__file__).resolve().parents[5] / "policy"
    with open(config_dir / "configurations" / f"{args.instrument.lower()}.yaml") as fp:
        import yaml

        config = yaml.safe_load(fp)

    # Compute double zernike sensitivity matrix
    sensitivity_matrix = get_sensitivity_dz(config, args.instrument, args.filter)

    # Save double zernike sensitivity matrix
    save_sensitivity_matrix(args.path, args.instrument, sensitivity_matrix)


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
        "--instrument",
        choices=["LSST", "ComCam"],
        default="LSST",
        help="Type of instrument to use",
    )

    return parser.parse_args()


def generate_intrinsic_zernikes() -> None:
    main(parse_arguments())
