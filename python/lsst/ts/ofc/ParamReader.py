import os
import numpy as np


class ParamReader(object):

    def __init__(self, filePath=None):
        """Initialization of parameter reader class.

        Parameters
        ----------
        filePath : str, optional
            File path. (the default is None.)
        """

        if (filePath is None):
            self.filePath = ""
        else:
            self.filePath = filePath

        self._content = self._readContent(self.filePath)

    def _readContent(self, filePath):
        """Read the content of file.

        Parameters
        ----------
        filePath : str
            File path.

        Returns
        -------
        str
            Content of file.
        """

        if (os.path.exists(filePath)):
            with open(filePath, "r") as file:
                content = file.read()
        else:
            content = ""

        return content

    def getFilePath(self):
        """Get the parameter file path.

        Returns
        -------
        str
            Get the file path.
        """

        return self.filePath

    def getTxtContent(self):
        """Get the text content.

        Returns
        -------
        str
            Text content.
        """

        return self._content

    def getMatContent(self, usecols=None):
        """Get the matrix content.

        Parameters
        ----------
        usecols: sequence, optional
            Which columns to read, with 0 being the first. (the default is
            None.)

        Returns
        -------
        numpy.ndarray
            Matrix content.
        """

        if (os.path.exists(self.filePath)):
            mat = np.loadtxt(self.filePath, usecols=usecols)
        else:
            mat = np.array([])

        return mat

    def getSetting(self, param, arrayParamList=[]):
        """Get the setting value.

        Parameters
        ----------
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
        content = self._content.splitlines()
        for line in content:
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


if __name__ == "__main__":
    pass
