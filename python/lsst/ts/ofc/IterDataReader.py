import os
import re
import numpy as np


class IterDataReader(object):
    """Iteration data reader to read the active optics simulation data."""

    def __init__(self, dataDir):
        """Initialization of class.

        Parameters
        ----------
        dataDir : str
            Simulation data directory.
        """

        self.dataDir = dataDir

    def setDataDir(self, dataDir):
        """Set the simulation data directory.

        Parameters
        ----------
        dataDir : str
            Simulation data directory.
        """

        self.dataDir = dataDir

    def _getIterDir(self, iterNum):
        """Get the directory of specific iteration data.

        Parameters
        ----------
        iterNum : int
            Iteration number.

        Returns
        -------
        str
            Path of iteration data directory.
        """

        iterDir = os.path.join(self.dataDir, "iter%d" % int(iterNum))

        return iterDir

    def _getDirFiles(self, dirPath):
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

    def _getIterFiles(self, iterNum):
        """Get the file paths in specific iteration number.

        Parameters
        ----------
        iterNum : int
            Iteration number.

        Returns
        -------
        list
            List of file paths.
        """

        return self._getDirFiles(self._getIterDir(iterNum))

    def _getMatchFilePath(self, reMatchStr, filePaths):
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
        RuntimeError
            Can not find the matched file.
        """

        # Look for the matched file by the regular expression
        matchFilePath = None
        for filePath in filePaths:

            fileName = os.path.basename(filePath)
            m = re.match(reMatchStr, fileName)

            if (m is not None):
                matchFilePath = filePath
                break

        # Raise the error if can not find the matched file
        if matchFilePath is None:
            raise RuntimeError("Cannot find the file.")

        return matchFilePath

    def _getMatchFilePathInIter(self, reMatchStr, iterNum):
        """Get the matched file path in specific iteration number.

        Parameters
        ----------
        reMatchStr : str
            Matching string for the regular expression.
        iterNum : int
            Iteration number.

        Returns
        -------
        str
            Matched file path.
        """

        filePaths = self._getIterFiles(iterNum)
        matchFilePath = self._getMatchFilePath(reMatchStr, filePaths)

        return matchFilePath

    def getAbsFilePathOfWfsErr(self, iterNum, reMatchStr=r"\w*E000.z4c"):
        """Get the absolute file path of wavefront error.

        Parameters
        ----------
        iterNum : int
            Iteration number.
        reMatchStr : str, optional
            Matching string for the regular expression. (the default is
            "w*E000.z4c", which is the LSST data.)

        Returns
        -------
        str
            Absolute file path of wavefront error.
        """

        matchFilePath = self._getMatchFilePathInIter(reMatchStr, iterNum)

        return os.path.abspath(matchFilePath)

    def getWfsErr(self, iterNum):
        """Get the wavefront error in specific iteration number.

        Parameters
        ----------
        iterNum : int
            Iteration number.

        Returns
        -------
        ndarray
            Wavefront error.
        """

        wfsFilePath = self.getAbsFilePathOfWfsErr(iterNum)

        wfsErr = np.loadtxt(wfsFilePath)
        wfsErr = wfsErr[:, 0:19]

        return wfsErr

    def getPssn(self, iterNum):
        """Get the PSSN in specific iteration number.

        PSSN: Normalized point source sensitivity.

        Parameters
        ----------
        iterNum : int
            Iteration number.

        Returns
        -------
        ndarray
            PSSN data.
        """

        reMatchStr = r"\w*PSSN.txt"
        matchFilePath = self._getMatchFilePathInIter(reMatchStr, iterNum)

        data = np.loadtxt(matchFilePath)
        pssn = data[0, 0:31]

        return pssn

    def getDof(self, iterNum):
        """Get the degree of freedom (DOF) in specific iteration number.

        Parameters
        ----------
        iterNum : int
            Iteration number.

        Returns
        -------
        ndarray
            DOF data.
        """

        reMatchStr = r"\w*pert.txt"
        matchFilePath = self._getMatchFilePathInIter(reMatchStr, iterNum)

        dof = np.loadtxt(matchFilePath, usecols=(2))

        return dof

    def getWfsSensorIdList(self):
        """Get the corner wavefront sensor Id list.

        Returns
        -------
        list
            Sensor Id list.
        """

        sensorIdList = [198, 31, 2, 169]

        return sensorIdList

    def getPssnSensorIdList(self):
        """Get the normalized point source sensitivity (PSSN) sensor Id list.

        Returns
        -------
        list
            Sensor Id list.
        """

        sensorIdList = [100, 103, 104, 105, 97, 96, 99, 140, 150, 117,
                        60, 46, 83, 173, 120, 61, 11, 38, 82, 176,
                        122, 116, 8, 35, 81, 179, 164, 70, 5, 33,
                        123]

        return sensorIdList


if __name__ == "__main__":
    pass
