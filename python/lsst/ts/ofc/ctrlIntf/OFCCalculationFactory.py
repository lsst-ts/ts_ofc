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
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfLsst import OFCCalculationOfLsst
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfComCam import OFCCalculationOfComCam
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfSh import OFCCalculationOfSh
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfCmos import OFCCalculationOfCmos
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfLsstFam import OFCCalculationOfLsstFam


class OFCCalculationFactory(object):
    """Factory for creating the correct OFC calculation based off the
    instrument currently being used.
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def getCalculator(instName, state0Dof=None):
        """Get a calculator to process wavefront error.

        Parameters
        ----------
        instName : enum 'InstName'
            The instrument to get the wavefront calculator for.
        state0Dof : dict, optional
            State 0 DoF dictionary. If None (=default), the instrument's
            default will be used. See
            :lsst:ts:ofc:`OptCtrlDataDecorator.getState0FromDict` for format
            details.

        Returns
        -------
        OFCCalculation child (e.g. OFCCalculationOfComCam)
            Concrete child class of OFCCalculation class.

        Raises
        ------
        ValueError
            This instrument is not supported.
        """

        if instName == InstName.LSST:
            return OFCCalculationOfLsst(state0Dof)
        elif instName == InstName.COMCAM:
            return OFCCalculationOfComCam(state0Dof)
        elif instName == InstName.SH:
            return OFCCalculationOfSh(state0Dof)
        elif instName == InstName.CMOS:
            return OFCCalculationOfCmos(state0Dof)
        elif instName == InstName.LSSTFAM:
            return OFCCalculationOfLsstFam(state0Dof)
        else:
            raise ValueError("This instrument is not supported.")
