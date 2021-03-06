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

from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfIota import OFCCalculationOfIota


class OFCCalculationOfCmos(OFCCalculationOfIota):
    """The concrete child class of OFCCalculation of the CMOS"""

    def __init__(self, state0Dof=None):
        """Construct an OFC calculation of CMOS camera.

        Parameters
        ----------
        state0Dof : dict, optional
            State 0 DoF dictionary. If None (=default), the instrument's
            default will be used. See
            :lsst:ts:ofc:`OptCtrlDataDecorator.getState0FromDict` for format
            details.

        CMOS: Complementary metal–oxide–semiconductor.
        """

        # Use the data in ComCam
        super().__init__(InstName.COMCAM, "cmos", state0Dof)
