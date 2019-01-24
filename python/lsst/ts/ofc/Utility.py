import os
import re
from enum import Enum
import lsst.ts.ofc


class InstName(Enum):
    LSST = 1
    COMCAM = 2


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


def getModulePath(module=lsst.ts.ofc, startIdx=1, endIdx=-4):
    """Get the path of module.

    Parameters
    ----------
    module : str, optional
        Module name. (the default is lsst.ts.ofc.)
    startIdx : int, optional
        Start index. (the default is 1.)
    endIdx : int, optional
        End index. (the default is -4.)

    Returns
    -------
    str
        Directory path of module based on the start and end indexes.
    """

    # Get the path of module
    modulePathList = os.path.dirname(module.__file__).split(
                                os.sep)[int(startIdx):int(endIdx)]
    modulePath = os.path.join(os.sep, *modulePathList)

    return modulePath


if __name__ == "__main__":
    pass
