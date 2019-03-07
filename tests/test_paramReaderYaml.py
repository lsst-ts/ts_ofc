import os
import unittest

from lsst.ts.ofc.ParamReaderYaml import ParamReaderYaml
from lsst.ts.ofc.Utility import getModulePath


class TestYamlParamReader(unittest.TestCase):
    """Test the YamlParamReader class."""

    def setUp(self):

        self.configDir = os.path.join(getModulePath(), "policy")
        self.fileName = "zkAndDofIdxArraySet.yaml"

        filePath = os.path.join(self.configDir, self.fileName)
        self.paramReader = ParamReaderYaml(filePath=filePath)

    def testGetSetting(self):
        global paramReader

        paramReader = self.paramReader


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
