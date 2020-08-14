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
from lsst.ts.wep.ctrlIntf.SensorWavefrontError import SensorWavefrontError

from lsst.ts.ofc.Utility import InstName, getModulePath
from lsst.ts.ofc.ctrlIntf.OFCCalculation import OFCCalculation
from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN
from lsst.ts.ofc.ctrlIntf.CameraHexapodCorrection import CameraHexapodCorrection
from lsst.ts.ofc.ctrlIntf.M2HexapodCorrection import M2HexapodCorrection
from lsst.ts.ofc.ctrlIntf.M1M3Correction import M1M3Correction
from lsst.ts.ofc.ctrlIntf.M2Correction import M2Correction
from lsst.ts.ofc.ctrlIntf.FWHMSensorData import FWHMSensorData
from lsst.ts.ofc.ZTAAC import ZTAAC


class TestOFCCalculation(unittest.TestCase):
    """Test the OFCCalculation class."""

    def setUp(self):

        self.ofcCalculation = OFCCalculation(FWHMToPSSN(), InstName.LSST)
        self.testDataDir = os.path.join(getModulePath(), "tests", "testData")

    def testInitDofFromLastVisit(self):

        ztaac = self.ofcCalculation.getZtaac()
        numOfState0 = ztaac.optCtrl.getNumOfState0()
        self.ofcCalculation.dofFromLastVisit = np.random.rand(numOfState0)

        self.ofcCalculation.initDofFromLastVisit()

        dofFromLastVisit = self.ofcCalculation.getStateCorrectionFromLastVisit()
        self.assertEqual(np.sum(np.abs(dofFromLastVisit)), 0)

    def testGetZtaac(self):

        self.assertTrue(isinstance(self.ofcCalculation.getZtaac(), ZTAAC))

    def testGetPssnData(self):

        pssnData = self.ofcCalculation.getPssnData()
        sensorId = pssnData["sensorId"]
        pssn = pssnData["pssn"]

        self.assertEqual(len(sensorId), 0)
        self.assertEqual(len(pssn), 0)

    def testSetFWHMSensorDataOfCam(self):

        fwhmValues = np.ones(19) * 0.2
        numOfSensor = 5
        listOfFWHMSensorData = []
        for sglSensorId in range(numOfSensor):
            fwhmSensorData = FWHMSensorData(sglSensorId, fwhmValues)
            listOfFWHMSensorData.append(fwhmSensorData)

        self.ofcCalculation.setFWHMSensorDataOfCam(listOfFWHMSensorData)

        pssnData = self.ofcCalculation.getPssnData()
        sensorId = pssnData["sensorId"]
        pssn = pssnData["pssn"]

        self.assertEqual(sensorId.tolist(), list(range(numOfSensor)))
        self.assertAlmostEqual(pssn[0], 0.9139012, places=6)

    def testGetFilter(self):

        self.assertEqual(self.ofcCalculation.getFilter(), FilterType.REF)

    def testSetFilter(self):

        filterType = FilterType.R
        self.ofcCalculation.setFilter(filterType)

        self.assertEqual(self.ofcCalculation.getFilter(), filterType)

    def testGetRotAng(self):

        self.assertEqual(self.ofcCalculation.getRotAng(), 0.0)

    def testSetRotAng(self):

        rotAng = 10.0
        self.ofcCalculation.setRotAng(rotAng)

        self.assertEqual(self.ofcCalculation.getRotAng(), rotAng)

    def testResetOfcState(self):

        numOfState0 = self.ofcCalculation.ztaac.optCtrl.getNumOfState0()
        dof = np.ones(numOfState0)
        self.ofcCalculation.ztaac.aggState(dof)
        self.ofcCalculation._setStateCorrectionFromLastVisit(dof)

        (
            m2HexapodCorrection,
            hexapodCorrection,
            m1m3Correction,
            m2Correction,
        ) = self.ofcCalculation.resetOfcState()

        self.assertTrue(isinstance(m2HexapodCorrection, M2HexapodCorrection))
        self.assertTrue(isinstance(hexapodCorrection, CameraHexapodCorrection))
        self.assertTrue(isinstance(m1m3Correction, M1M3Correction))
        self.assertTrue(isinstance(m2Correction, M2Correction))

        self.assertEqual(np.sum(m2HexapodCorrection.getCorrection()), 0)
        self.assertEqual(np.sum(hexapodCorrection.getCorrection()), 0)
        self.assertEqual(np.sum(m1m3Correction.getZForces()), 0)
        self.assertEqual(np.sum(m2Correction.getZForces()), 0)

        dofFromLastVisit = self.ofcCalculation.getStateCorrectionFromLastVisit()

        self.assertEqual(len(dofFromLastVisit), 50)
        self.assertEqual(np.sum(np.abs(dofFromLastVisit)), 0)

    def testSetGainByUser(self):

        self.assertEqual(self.ofcCalculation.useGainByPssn, True)
        self.assertEqual(self.ofcCalculation.getGainInUse(), 0.0)

        gainByUser = 0.5
        self._setGainByUser(gainByUser)
        self.assertEqual(self.ofcCalculation.useGainByPssn, False)
        self.assertEqual(self.ofcCalculation.getGainInUse(), gainByUser)

    def _setGainByUser(self, gainByUser):

        self.ofcCalculation.setGainByUser(gainByUser)

        return gainByUser

    def testSetGainByUserWithBadValue(self):

        gainByUser = 1.3
        self.assertRaises(ValueError, self.ofcCalculation.setGainByUser, gainByUser)

    def testSetGainByUserWithDefaultValue(self):

        gainByUser = -1
        self._setGainByUser(gainByUser)

        self.assertEqual(self.ofcCalculation.useGainByPssn, True)

    def testSetGainByPSSN(self):

        gainByUser = 0.5
        self._setGainByUser(gainByUser)

        self.ofcCalculation.setGainByPSSN()
        self.assertEqual(self.ofcCalculation.useGainByPssn, True)

    def testCalculateCorrectionsWithUserGain(self):

        gainByUser = 1
        self.ofcCalculation.setGainByUser(gainByUser=gainByUser)

        listOfWfErr = self._getListOfSensorWavefrontError()

        (
            m2HexapodCorrection,
            hexapodCorrection,
            m1m3Correction,
            m2Correction,
        ) = self.ofcCalculation.calculateCorrections(listOfWfErr)

        self.assertTrue(isinstance(m2HexapodCorrection, M2HexapodCorrection))
        self.assertTrue(isinstance(hexapodCorrection, CameraHexapodCorrection))
        self.assertTrue(isinstance(m1m3Correction, M1M3Correction))
        self.assertTrue(isinstance(m2Correction, M2Correction))

        uk = self.ofcCalculation.getStateCorrectionFromLastVisit()

        self.assertAlmostEqual(uk[0], -9.44847541, places=7)
        self.assertAlmostEqual(uk[1], -2.53792714, places=7)
        self.assertAlmostEqual(uk[5], -39.91899739, places=7)
        self.assertAlmostEqual(uk[7], 3.25321204, places=7)

    def _getListOfSensorWavefrontError(self):

        wfErr, sensorNameList = self._getWfErrAndSensorNameListFromLsstFile()
        sensorIdList = self.ofcCalculation.ztaac.mapSensorNameToId(sensorNameList)

        listOfWfErr = []
        for sensorId, annularZernikePoly in zip(sensorIdList, wfErr):
            sensorWavefrontError = SensorWavefrontError(numOfZk=19)
            sensorWavefrontError.setSensorId(sensorId)
            sensorWavefrontError.setAnnularZernikePoly(annularZernikePoly)
            listOfWfErr.append(sensorWavefrontError)

        return listOfWfErr

    def _getWfErrAndSensorNameListFromLsstFile(self):

        wfFilePath = os.path.join(self.testDataDir, "lsst_wfs_error_iter0.z4c")
        sensorNameList = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]
        wfErr = self.ofcCalculation.ztaac.getWfFromFile(wfFilePath, sensorNameList)

        return wfErr, sensorNameList

    def testGetStateCorrectionFromLastVisit(self):

        ansStateCorrection = self._setStateCorrectionFromLastVisitWithSpecificDofIdx()
        stateCorrection = self.ofcCalculation.getStateCorrectionFromLastVisit()

        self.assertTrue(isinstance(stateCorrection, np.ndarray))
        self.assertEqual(
            len(stateCorrection), self.ofcCalculation.ztaac.optCtrl.getNumOfState0()
        )

        delta = np.sum(np.abs(stateCorrection - ansStateCorrection))
        self.assertEqual(delta, 0)

    def _setStateCorrectionFromLastVisitWithSpecificDofIdx(self):

        m2HexPos = np.zeros(5, dtype=int)
        camHexPos = np.ones(5, dtype=int)
        m1m3Bend = np.zeros(20, dtype=int)
        m2Bend = np.zeros(20, dtype=int)
        self.ofcCalculation.ztaac.setZkAndDofInGroups(
            m2HexPos=m2HexPos, camHexPos=camHexPos, m1m3Bend=m1m3Bend, m2Bend=m2Bend
        )

        calcDof = np.arange(1, 6)
        self.ofcCalculation._setStateCorrectionFromLastVisit(calcDof)

        rearangedDof = np.zeros(50)
        rearangedDof[5:10] = calcDof

        return rearangedDof

    def testGetStateAggregated(self):

        stateAns = self._setStateAggregated()

        stateAgg = self.ofcCalculation.getStateAggregated()

        self.assertTrue(isinstance(stateAgg, np.ndarray))
        self.assertEqual(len(stateAgg), 50)

        delta = np.sum(np.abs(stateAgg - stateAns))

        self.assertEqual(delta, 0)

    def _setStateAggregated(self):

        numOfState0 = self.ofcCalculation.ztaac.optCtrl.getNumOfState0()
        state = np.arange(numOfState0)

        self.ofcCalculation.ztaac.aggState(state)

        return state


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
