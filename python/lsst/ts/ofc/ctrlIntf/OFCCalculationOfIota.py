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

import os

from lsst.ts.ofc.ctrlIntf.OFCCalculation import OFCCalculation
from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN


class OFCCalculationOfIota(OFCCalculation):
    """The concrete child class of OFCCalculation of IOTA."""

    def __init__(self, instName, specificInstDirName, state0Dof=None):
        """Construct an OFC calculation of IOTA.

        IOTA: Initial optical test assembly.

        Parameters
        ----------
        instName : enum 'InstName'
            Instrument name.
        specificInstDirName : str
            Specific instrument directory name.
        state0Dof : dict, optional
            State 0 DoF dictionary. If None (=default), the instrument's
            default will be used. See
            :lsst:ts:ofc:`OptCtrlDataDecorator.getState0FromDict` for format
            details.
        """

        super(OFCCalculationOfIota, self).__init__(FWHMToPSSN(), instName, state0Dof)

        # Set the idx of zk and DOF
        self._setZkAndDofIdxOfIota(specificInstDirName, instName)

    def _setZkAndDofIdxOfIota(self, specificInstDirName, instName):
        """Set the Z3-Zn and DOF indexes of specific IOTA camera.

        DOF: degree of freedom.
        IOTA: Initial optical test assembly.

        Parameters
        ----------
        specificInstDirName : str
            Specific instrument directory name.
        instName : enum 'InstName'
            Instrument name.
        """

        configDir = self.ztaac.dataShare.getConfigDir()
        zkAndDofIdxArraySetFile = self.ztaac.dataShare._zkAndDofIdxArraySetFile
        zkAndDofIdxArraySetFilePath = zkAndDofIdxArraySetFile.getFilePath()
        zkAndDofIdxArraySetFileName = os.path.basename(zkAndDofIdxArraySetFilePath)

        specificZkAndDofIdxArraySetFileName = os.path.join(
            specificInstDirName, zkAndDofIdxArraySetFileName
        )
        self.ztaac.dataShare.config(
            configDir,
            instName,
            zkAndDofIdxArraySetFileName=specificZkAndDofIdxArraySetFileName,
        )


if __name__ == "__main__":
    pass
