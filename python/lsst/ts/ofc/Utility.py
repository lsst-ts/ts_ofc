import os
import re
from enum import Enum
import lsst.ts.ofc


class InstName(Enum):
    LSST = 1
    COMCAM = 2


class FilterType(Enum):
    U = 1
    G = 2
    R = 3
    I = 4
    Z = 5
    Y = 6
    REF = 7


class DofGroup(Enum):
    M2HexPos = 1
    CamHexPos = 2
    M1M3Bend = 3
    M2Bend = 4


def getSetting(filePath, param, arrayParamList=[]):
    """Get the setting value.

    Parameters
    ----------
    filePath : str
        File path.
    param : str
        Parameter name.
    arrayParamList : list, optional
        List of parameter names that the value is an array
        instead of single value. (the default is [], which
        means no array parameters in file.)

    Returns
    -------
    str
        Parameter value.

    Raises
    ------
    ValueError
        No setting value is found.
    """

    val = None
    lineCount = 0
    assignedLine = -1
    with open(filePath) as file:
        for line in file:
            line = line.strip()

            # Skip the comment or empty line
            if line.startswith("#") or (len(line) == 0):
                continue

            if line.startswith(param):
                val = line.split()[1:]

            if (val is not None) and (len(val) == 1):
                val = val[0]

            # Search for the array value if necessary
            if (val is not None) and (param in arrayParamList):
                assignedLine = int(val)
                val = None

            if (val is None) and (assignedLine > -1):
                if (lineCount != assignedLine):
                    lineCount += 1
                else:
                    val = line

            # Stop search if the value is found
            if (val is not None):
                break

    if (val is None):
        raise ValueError("Can not find the setting of %s." % param)

    return val


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
        m = re.match(r"%s" % reMatchStr, fileName)

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
