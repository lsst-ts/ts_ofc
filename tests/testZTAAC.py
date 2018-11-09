import os
import numpy as np
import unittest

from lsst.ts.ofc.Utility import InstName, FilterType, DofGroup
from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator
from lsst.ts.ofc.OptStateEsti import OptStateEsti
from lsst.ts.ofc.OptCtrl import OptCtrl
from lsst.ts.ofc.CamRot import CamRot
from lsst.ts.ofc.ZTAAC import ZTAAC


if __name__ == "__main__":

    # # Run the unit test
    # unittest.main()
    
    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"

    dataShare = DataShare()
    dataShare.config(configDir, instName=InstName.LSST)

    optStateEstiDataDecorator = OptStateEstiDataDecorator(dataShare)
    optStateEstiDataDecorator.configOptStateEstiData()

    mixedData = OptCtrlDataDecorator(optStateEstiDataDecorator)
    mixedData.configOptCtrlData()

    optStateEsti = OptStateEsti()
    optCtrl = OptCtrl()

    ztaac = ZTAAC(optStateEsti, optCtrl, mixedData)
    ztaac.config(filterType=FilterType.REF)

    gain = 1.0
    ztaac.setGain(gain)

    state0InDof = ztaac.setState0FromFile()
    ztaac.setStateToState0()

    testDataDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/tests/testData"
    testWfsFile = "lsst_wfs_error_iter0.z4c"
    testWfsFilePath = os.path.join(testDataDir, testWfsFile)

    sensorNameList = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]
    wfErr = ztaac.getWfFromFile(testWfsFilePath, sensorNameList)
    uk = ztaac.estiUkWithGain(wfErr, sensorNameList)
    print(uk)

    ztaac.aggState(uk)
    print(ztaac.getGroupDof(DofGroup.M2HexPos))
    print(ztaac.getGroupDof(DofGroup.CamHexPos))
    print(ztaac.getGroupDof(DofGroup.M2Bend))
    print(ztaac.getGroupDof(DofGroup.M1M3Bend))
