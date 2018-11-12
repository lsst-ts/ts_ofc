import unittest

from lsst.ts.ofc.Decorator import Decorator


class TempObj(object):

    def __init__(self):
        self.a = 0

    def addA(self):
        self.a += 1

    def getA(self):
        return self.a


class TempDecorator(Decorator):

    def __init__(self, decoratedObj, b):
        super(TempDecorator, self).__init__(decoratedObj)
        self.b = b

    def minusA(self):
        self.a -= 1

    def getB(self):
        return self.b


class TestDecorator(unittest.TestCase):
    """Test the Decorator class."""

    def setUp(self):
        obj = TempObj()
        self.decorator = TempDecorator(obj, 3)

    def testDecoratoredObj(self):
        self.assertEqual(self.decorator.getA(), 0)

        self.decorator.addA()
        self.assertEqual(self.decorator.getA(), 1)

    def testDecorator(self):
        self.assertEqual(self.decorator.getB(), 3)

        self.decorator.minusA()
        self.assertEqual(self.decorator.getA(), 0)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
