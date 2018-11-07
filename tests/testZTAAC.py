import os
import numpy as np
import unittest

from lsst.ts.ofc.OptStateEsti import InstName, FilterType, DofGroup
from lsst.ts.ofc.OptStateEsti import OptStateEsti
from lsst.ts.ofc.OptCtrl import OptCtrl
from lsst.ts.ofc.CamRot import CamRot
from lsst.ts.ofc.ZTAAC import ZTAAC


if __name__ == "__main__":

    # # Run the unit test
    # unittest.main()
    
    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"

    optStateEsti = OptStateEsti()
    optStateEsti.config(configDir, instName=InstName.LSST)

    optCtrl = OptCtrl()
    optCtrl.config(configDir, instName=InstName.LSST,
                   configFileName="optiPSSN_x00.ctrl")

    ztaac = ZTAAC(optStateEsti, optCtrl)
    ztaac.config(configDir)

    gain = 0.7
    ztaac.setGain(gain)

    # ztaac.setState0(np.random.rand(50))
    # state0 = ztaac.getState0()
    # ztaac.setStateToState0()

    sensorIdList = [1, 2, 3, 4, 5, -1, -1]
    sensorNameList, numOfSensor = ztaac.mapSensorIdToName(sensorIdList)
    sensorIdList = ztaac.mapSensorNameToId(sensorNameList)
    
    pssn = np.ones(31)*0.7
    sensorIdList = [100, 103, 104, 105, 97, 96, 95, 140, 150, 109, 44, 46,
                    93, 180, 120, 118, 18, 45, 82, 183, 122, 116, 24, 40,
                    81, 179, 161, 70, 5, 33, 123]
    sensorNameList, numOfSensor = ztaac.mapSensorIdToName(sensorIdList)

    ztaac.setGainByPSSN(pssn, sensorNameList)

    testDataDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/tests/testData"
    testWfsFile = "lsst_wfs_error_iter0.z4c"
    testWfsFilePath = os.path.join(testDataDir, testWfsFile)

    wfErr = ztaac.getWfFromFile(testWfsFilePath)
    ztaac.setFilter(FilterType.REF)
    sensorNameList = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]

    uk = ztaac.estiUk(wfErr, sensorNameList)
    ztaac.aggState(uk)

    dof = ztaac.getGroupDof(DofGroup.M2HexPos)
    print(dof)

    camRot = CamRot(rotAngInDeg=45)
    rotUk = ztaac.rotUk(camRot, uk)
    print(rotUk) 