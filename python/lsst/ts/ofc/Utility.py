import os
import re
from enum import Enum

from lsst.utils import getPackageDir


class InstName(Enum):
    LSST = 1
    COMCAM = 2
    SH = 3
    CMOS = 4


class DofGroup(Enum):
    M2HexPos = 1
    CamHexPos = 2
    M1M3Bend = 3
    M2Bend = 4


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

    onlyFiles = [f for f in os.listdir(dirPath)
                 if os.path.isfile(os.path.join(dirPath, f))]
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

        if (m is not None):
            matchFilePath = filePath
            break

    if (matchFilePath is None):
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


if __name__ == "__main__":
    pass
