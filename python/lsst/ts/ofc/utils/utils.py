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

__all__ = ["get_pkg_root", "get_config_dir", "rot_1d_array", "get_field_angles"]

import pathlib
from typing import List, Tuple

import lsst.obs.lsst as obs_lsst
import numpy as np
from lsst.afw.cameraGeom import FIELD_ANGLE


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


def get_field_angles(sensor_names: list) -> Tuple[List[float], List[float]]:
    """Get the field angle for a given sensor name.

    Parameters
    ----------
    sensor_names : list [str]
        List of sensor names.

    Returns
    -------
    field_x : list [float]
        List of field x angles in degrees.
    field_y : list [float]
        List of field y angles in degrees.
    """

    # Create camera object
    camera = obs_lsst.LsstCam().getCamera()

    # Get the field angle for each sensor
    field_list = list()
    for name in sensor_names:
        # If it is a wavefront corner sensor, get the center
        # between the extra and intra focal sensors.
        # Otherwise, get the center of the sensor.
        if name in ["R00_SW0", "R40_SW0", "R04_SW0", "R44_SW0"]:
            # Get center of the extra focal sensor.
            extra_field_point = camera.get(name).getCenter(FIELD_ANGLE)

            # Get center of the intra focal sensor.
            detector_id = camera.get(name).getId() + 1
            detector_map = camera.getIdMap()
            intra_field_point = detector_map[detector_id].getCenter(FIELD_ANGLE)

            # Compute mean between intra and extra focal sensor.
            center_field_point = np.mean([extra_field_point, intra_field_point], axis=0)

        else:
            # Get center of the sensor.
            center_field_point = camera.get(name).getCenter(FIELD_ANGLE)

        # Switch X,Y coordinates to convert from DVCS to CCS coords.
        field_list.append(
            (-np.degrees(center_field_point[1]), np.degrees(center_field_point[0]))
        )

    # Return the field angles field_x and field_y
    return field_list
