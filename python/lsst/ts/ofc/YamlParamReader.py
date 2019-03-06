import yaml


class YamlParamReader(object):

    def __init__(self, filePath=None):
        """Initialization of yaml parameter reader class.

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

        with open(filePath, "r") as yamlFile:
            content = yaml.load(yamlFile)

        return content

    def getSetting(self, param):

        val = self._content[param]

        return val


if __name__ == "__main__":
    pass
