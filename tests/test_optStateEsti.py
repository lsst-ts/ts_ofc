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
import numpy as np
import unittest

from lsst.ts.wep.Utility import FilterType

from lsst.ts.ofc.Utility import InstName, getModulePath, getConfigDir
from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator
from lsst.ts.ofc.OptStateEsti import OptStateEsti


class TestOptStateEsti(unittest.TestCase):
    """Test the OptStateEsti class."""

    def setUp(self):

        dataShare = DataShare()
        configDir = getConfigDir()
        dataShare.config(configDir, instName=InstName.LSST)

        self.optStateEstiData = OptStateEstiDataDecorator(dataShare)
        self.optStateEstiData.configOptStateEstiData()

        self.optStateEsti = OptStateEsti()

        wfsFilePath = os.path.join(
            getModulePath(), "tests", "testData", "lsst_wfs_error_iter0.z4c"
        )
        sensorNameList = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]
        wfErr, fieldIdx = self.optStateEstiData.getWfAndFieldIdFromFile(
            wfsFilePath, sensorNameList
        )
        self.wfErr = wfErr
        self.fieldIdx = fieldIdx

    def testEstiOptState(self):

        optState = self.optStateEsti.estiOptState(
            self.optStateEstiData, FilterType.REF, self.wfErr, self.fieldIdx
        )
        dofIdx = self.optStateEstiData.getDofIdx()

        self.assertEqual(len(optState), len(dofIdx))
        self.assertAlmostEqual(optState[0], 29.82660072, places=7)
        self.assertAlmostEqual(optState[1], 0.05548614, places=7)
        self.assertAlmostEqual(optState[2], -0.03946648, places=7)

    def testEstiOptStateWithDifferentZkIdxAndDofIdx(self):

        zn3Idx = np.arange(5)
        dofIdx = np.arange(10)
        self.optStateEstiData.setZkAndDofIdxArrays(zn3Idx, dofIdx)

        optState = self.optStateEsti.estiOptState(
            self.optStateEstiData, FilterType.REF, self.wfErr, self.fieldIdx
        )
        self.assertEqual(len(optState), len(dofIdx))
        self.assertAlmostEqual(optState[0], -645.7540849494324)
        self.assertAlmostEqual(optState[1], -10221.082801186029)
        self.assertAlmostEqual(optState[2], -758.518174)

    def testEstiOptStateWithoutEnoughZk(self):

        zn3Idx = np.arange(4)
        dofIdx = np.arange(20)
        self.optStateEstiData.setZkAndDofIdxArrays(zn3Idx, dofIdx)

        self.assertRaises(
            RuntimeError,
            self.optStateEsti.estiOptState,
            self.optStateEstiData,
            FilterType.REF,
            self.wfErr,
            self.fieldIdx,
        )


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
