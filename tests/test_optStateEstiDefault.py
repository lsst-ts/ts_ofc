import unittest

from lsst.ts.ofc.OptStateEstiDefault import OptStateEstiDefault


class TestOptStateEstiDefault(unittest.TestCase):
    """Test the OptStateEstiDefault class."""

    def setUp(self):
        self.optStateEsti = OptStateEstiDefault()

    def testEstiOptState(self):
        self.assertRaises(NotImplementedError,
                          self.optStateEsti.estiOptState,
                          None, None, None, None)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
