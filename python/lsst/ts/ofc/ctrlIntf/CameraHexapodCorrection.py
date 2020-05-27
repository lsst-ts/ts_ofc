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


class CameraHexapodCorrection(object):
    """Contains the correction for MT Hexapod."""

    def __init__(self, x, y, z, u, v, w=0.0):
        """Construct a Hexapod correction.

        Parameters
        ----------
        x : float
            The X position offset in um.
        y : float
            The Y position offset in um.
        z : float
            The Z position offset in um.
        u : float
            The X rotation offset in deg.
        v : float
            The Y rotation offset in deg.
        w : float (optional)
            The Z rotation offset in deg. (the default is 0.0)
        """

        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.u = 0.0
        self.v = 0.0
        self.w = 0.0

        self.setCorrection(x, y, z, u, v, w)

    def setCorrection(self, x, y, z, u, v, w=0.0):
        """Set the hexapod correction.

        Parameters
        ----------
        x : float
            The X position offset in um.
        y : float
            The Y position offset in um.
        z : float
            The Z position offset in um.
        u : float
            The X rotation offset in deg.
        v : float
            The Y rotation offset in deg.
        w : float, optional
            The Z rotation offset in deg. (the default is 0.0.)
        """

        self.x = x
        self.y = y
        self.z = z
        self.u = u
        self.v = v
        self.w = w

    def getCorrection(self):
        """Get the hexapod correction.

        Returns
        -------
        float
            The X position offset in um.
        float
            The Y position offset in um.
        float
            The Z position offset in um.
        float
            The X rotation offset in deg.
        float
            The Y rotation offset in deg.
        float
            The Z rotation offset in deg.
        """

        return self.x, self.y, self.z, self.u, self.v, self.w


if __name__ == "__main__":
    pass
