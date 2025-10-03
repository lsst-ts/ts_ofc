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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__all__ = ["get_pkg_root", "get_config_dir", "get_filter_name", "rot_1d_array"]

import pathlib

import numpy as np


def get_pkg_root() -> pathlib.Path:
    """Return the root directory of this package.

    Returns
    -------
    `pathlib.Path`
        Path to the package root.
    """
    return pathlib.Path(__file__).resolve().parents[1]


def get_config_dir() -> pathlib.Path:
    """Return the path to the ``policy`` dir within this package.

    Returns
    -------
    `pathlib.Path`
        Path to the package config directory.
    """
    return get_pkg_root() / "policy"


def get_filter_name(filter_name: str) -> str:
    """Return the filter name in the format used by the OFC.

    Parameters
    ----------
    filter_name : `str`
        Filter name.

    Returns
    -------
    `str`
        Filter name in the format used by the OFC.
    """
    if "_" in filter_name:
        return filter_name.split("_")[0].upper()
    else:
        return filter_name.upper()


def rot_1d_array(array: np.ndarray[float], rot_mat: np.ndarray[float]) -> np.ndarray:
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
