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

import numpy as np


class M2Correction(object):
    """Contains the correction for MT M2."""

    NUM_OF_ACT = 72

    def __init__(self, zForces):
        """Construct a M2 correction.

        Parameters
        ----------
        zForces : numpy.ndarray[72] (float)
            The forces to apply to the 72 axial actuators in N.
        """

        self.zForces = np.zeros(self.NUM_OF_ACT)
        self.setZForces(zForces)

    def setZForces(self, zForces):
        """Set the M2 zForces.

        Parameters
        ----------
        zForces : numpy.ndarray[72] (float)
            The forces to apply to the 72 axial actuators in N.

        Raises
        ------
        ValueError
            zForces must be an array of 72 floats.
        """

        if len(zForces) != self.NUM_OF_ACT:
            raise ValueError("zForces must be an array of %d floats." % self.NUM_OF_ACT)
        self.zForces = zForces

    def getZForces(self):
        """Get the M2 zForces.

        Returns
        -------
        numpy.ndarray[72] (float)
            The forces to apply to the 72 axial actuators in N.
        """

        return self.zForces


if __name__ == "__main__":
    pass
