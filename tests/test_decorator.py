# This file is part of ts_ofc.
#
# Developed for the LSST Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
