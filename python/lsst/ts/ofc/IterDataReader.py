import os
import re
import numpy as np


class IterDataReader(object):
    """Iteration data reader to read the active optics simulation data."""

    NUM_ZK = 19

    def __init__(self, dataDir):
        """Initialization of class.

        Parameters
        ----------
        dataDir : str
            Simulation data directory.
        """

        self.dataDir = dataDir

    def getAbsFilePathOfWfsErr(self, iterNum, reMatchStr=r"wfs.zer"):
        """Get the absolute file path of wavefront error.

        Parameters
        ----------
        iterNum : int
            Iteration number.
        reMatchStr : str, optional
            Matching string for the regular expression. (the default is
            r"wfs.zer", which is the ComCam data.)

        Returns
        -------
        str
            Absolute file path of wavefront error.
        """

        matchFilePath = self._getMatchFilePathInIter(iterNum, reMatchStr)

        return os.path.abspath(matchFilePath)

    def _getMatchFilePathInIter(self, iterNum, reMatchStr):
        """Get the matched file path in specific iteration number.

        Parameters
        ----------
        iterNum : int
            Iteration number.
        reMatchStr : str
            Matching string for the regular expression.

        Returns
        -------
        str
            Matched file path.
        """

        filePaths = self._getIterFiles(iterNum)

        return self._getMatchFilePath(filePaths, reMatchStr)

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

        return [os.path.join(dirPath, f) for f in onlyFiles]

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

        return os.path.join(self.dataDir, "iter%d" % int(iterNum))

    def _getMatchFilePath(self, filePaths, reMatchStr):
        """Get the matched file path.

        Parameters
        ----------
        filePaths : list
            File paths.
        reMatchStr : str
            Matching string for the regular expression.

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

    def getWfsErr(self, iterNum, reMatchStr=r"wfs.zer"):
        """Get the wavefront error in specific iteration number.

        Parameters
        ----------
        iterNum : int
            Iteration number.
        reMatchStr : str, optional
            Matching string for the regular expression. (the default is
            r"wfs.zer", which is the ComCam data.)

        Returns
        -------
        numpy.ndarray
            Wavefront error.
        """

        wfsFilePath = self.getAbsFilePathOfWfsErr(iterNum,
                                                  reMatchStr=reMatchStr)
        wfsErr = np.loadtxt(wfsFilePath)

        return wfsErr[:, 0:self.NUM_ZK]

    def getPssn(self, iterNum, numOfPssn, reMatchStr=r"PSSN.txt"):
        """Get the PSSN in specific iteration number.

        PSSN: Normalized point source sensitivity.

        Parameters
        ----------
        iterNum : int
            Iteration number.
        numOfPssn : int
            Number of PSSN elements.
        reMatchStr : str, optional
            Matching string for the regular expression. (the default is
            r"PSSN.txt", which is the ComCam data.)

        Returns
        -------
        numpy.ndarray
            PSSN data.
        """

        data = self._getImgQualData(iterNum, reMatchStr)

        return data[0, 0:numOfPssn]

    def _getImgQualData(self, iterNum, reMatchStr):
        """Get the image quality data.

        Parameters
        ----------
        iterNum : int
            Iteration number.
        reMatchStr : str
            Matching string for the regular expression.

        Returns
        -------
        numpy.ndarray
            Image quality data.
        """

        matchFilePath = self._getMatchFilePathInIter(iterNum, reMatchStr)

        return np.loadtxt(matchFilePath)

    def getFwhm(self, iterNum, numOfFwhm, reMatchStr=r"PSSN.txt"):
        """Get the FWHM in specific iteration number.

        FWHM: Full width at half maximum.

        Parameters
        ----------
        iterNum : int
            Iteration number.
        numOfFwhm : int
            Number of FWHM elements.
        reMatchStr : str, optional
            Matching string for the regular expression. (the default is
            r"PSSN.txt", which is the ComCam data.)

        Returns
        -------
        numpy.ndarray
            FWHM data.
        """

        data = self._getImgQualData(iterNum, reMatchStr)

        return data[1, 0:numOfFwhm]

    def getDof(self, iterNum, reMatchStr=r"dofPertInNextIter.mat"):
        """Get the degree of freedom (DOF) in specific iteration number.

        Parameters
        ----------
        iterNum : int
            Iteration number.
        reMatchStr : str, optional
            Matching string for the regular expression. (the default is
            r"dofPertInNextIter.mat", which is the ComCam data.)

        Returns
        -------
        numpy.ndarray
            DOF data.
        """

        matchFilePath = self._getMatchFilePathInIter(iterNum, reMatchStr)

        return np.loadtxt(matchFilePath)

    def getSensorIdListWfs(self):
        """Get the sensor Id list of corner wavefront sensor.

        Returns
        -------
        list [int]
            Sensor Id list.
        """

        return [198, 31, 2, 169]

    def getSensorIdListComCam(self):
        """Get the sensor Id list of commissioning camera.

        Returns
        -------
        list [int]
            Sensor Id list.
        """

        return list(range(96, 105))

    def getPssnSensorIdListWfs(self):
        """Get the normalized point source sensitivity (PSSN) sensor Id list of
        corner wavefront sensor.

        Returns
        -------
        list [int]
            Sensor Id list.
        """

        return [100, 103, 104, 105, 97, 96, 99, 140, 150, 117, 60, 46, 83, 173,
                120, 61, 11, 38, 82, 176, 122, 116, 8, 35, 81, 179, 164, 70, 5,
                33, 123]

    def getPssnSensorIdListComCam(self):
        """Get the normalized point source sensitivity (PSSN) sensor Id list of
        commissioning camera.

        Returns
        -------
        list [int]
            Sensor Id list.
        """

        return self.getSensorIdListComCam()


if __name__ == "__main__":
    pass
