# This file is part of ts_ofc
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

__all__ = ["get_pkg_root", "get_config_dir", "rot_1d_array"]

import pathlib


def get_pkg_root():
    """Return the root directory of this package.

    Returns
    -------
    `pathlib.PosixPath`
        Path to the package root.
    """
    return pathlib.Path(__file__).resolve().parents[5]


def get_config_dir():
    """Return the path to the ``policy`` dir within this package.

    Returns
    -------
    `pathlib.PosixPath`
        Path to the package config directory.
    """
    return get_pkg_root() / "policy"


def rot_1d_array(array, rot_mat):
    """Rotate 1D array from one basis to another.

    Parameters
    ----------
    array : `numpy.ndarray`
        1D array.
    rot_mat : `numpy.ndarray`
        Rotation matrix.

    Returns
    -------
    `numpy.ndarray`
        Rotated array in another basis compared with the original one.
    """

    array2d = array.reshape(-1, 1)
    rot_array = rot_mat.dot(array2d)

    return rot_array.ravel()