# This file is part of ts_ofc.
#
# Developed for the LSST Telescope and Site Systems.
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

import os
import re
from enum import IntEnum, auto

from lsst.utils import getPackageDir


class InstName(IntEnum):
    LSST = 1
    COMCAM = auto()
    SH = auto()
    CMOS = auto()
    LSSTFAM = auto()


class DofGroup(IntEnum):
    M2HexPos = 1
    CamHexPos = auto()
    M1M3Bend = auto()
    M2Bend = auto()


def getDirFiles(dirPath):
    """Get the file paths in the directory.

    Parameters
    ----------
    dirPath : str
        Directory path.

    Returns
    -------
    list
        List of file paths.
    """

    onlyFiles = [
        f for f in os.listdir(dirPath) if os.path.isfile(os.path.join(dirPath, f))
    ]
    filePaths = [os.path.join(dirPath, f) for f in onlyFiles]

    return filePaths


def getMatchFilePath(reMatchStr, filePaths):
    """Get the matched file path.

    Parameters
    ----------
    reMatchStr : str
        Matching string for the regular expression.
    filePaths : list
        File paths.

    Returns
    -------
    str
        Matched file path.

    Raises
    ------
    FileNotFoundError
        Cannot find the matched file.
    """

    # Look for the matched file
    matchFilePath = None
    for filePath in filePaths:

        fileName = os.path.basename(filePath)
        m = re.match(reMatchStr, fileName)

        if m is not None:
            matchFilePath = filePath
            break

    if matchFilePath is None:
        raise FileNotFoundError("Cannot find the matched file.")

    return matchFilePath


def rot1dArray(array, rotMat):
    """Rotate 1D array from one basis to another.

    Parameters
    ----------
    array : numpy.ndarray
        1D array.
    rotMat : numpy.ndarray
        Rotation matrix.

    Returns
    -------
    numpy.ndarray
        Rotated array in another basis compared with the original one.
    """

    array2d = array.reshape(-1, 1)
    rotArray = rotMat.dot(array2d)

    return rotArray.ravel()


def getModulePath():
    """Get the path of module.

    Returns
    -------
    str
        Directory path of module.
    """

    return getPackageDir("ts_ofc")


def getConfigDir():
    """Get the directory of configuration files.

    Returns
    -------
    str
        Directory of configuration files.
    """

    return os.path.join(getModulePath(), "policy")
