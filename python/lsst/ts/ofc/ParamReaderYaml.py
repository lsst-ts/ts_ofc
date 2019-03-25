import os
import numpy as np
import yaml


class ParamReaderYaml(object):

    def __init__(self, filePath=None):
        """Initialization of parameter reader of yaml format class.

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
        dict
            Content of file.
        """

        if (os.path.exists(filePath)):
            with open(filePath, "r") as yamlFile:
                content = yaml.safe_load(yamlFile)
        else:
            content = dict()

        return content

    def getFilePath(self):
        """Get the parameter file path.

        Returns
        -------
        str
            Get the file path.
        """

        return self.filePath

    def setFilePath(self, filePath):
        """Set the file path.

        Parameters
        ----------
        filePath : str
            File path.
        """

        self.__init__(filePath=filePath)

    def getContent(self):
        """Get the content.

        Returns
        -------
        list or dict
            Content.
        """

        return self._content

    def getSetting(self, param):
        """Get the setting value.

        Parameters
        ----------
        str
            Parameter name.

        Returns
        -------
        int, float, list, or dict
            Parameter value.
        """

        return self._content[param]

    @staticmethod
    def writeMatToFile(matrix, filePath):
        """Write the matrix data to file.

        Parameters
        ----------
        matrix : numpy.ndarray
            Matrix data.
        filePath : str
            Yaml file path.

        Raises
        ------
        ValueError
            The file name should end with '.yaml'.
        """

        if filePath.endswith(".yaml"):
            with open(filePath, "w") as yamlFile:
                yaml.safe_dump(matrix.tolist(), yamlFile)
        else:
            raise ValueError("The file name should end with '.yaml'.")

    def getMatContent(self):
        """Get the matrix content.

        Returns
        -------
        numpy.ndarray
            Matrix content.
        """

        if (self._content == dict()):
            mat = np.array([])
        else:
            mat = np.array(self._content)

        return mat


if __name__ == "__main__":
    pass
