import os
import numpy as np
import unittest

from lsst.ts.ofc.Utility import InstName, FilterType

from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator

from lsst.ts.ofc.OptStateEsti import OptStateEsti
from lsst.ts.ofc.OptCtrl import OptCtrl

if __name__ == "__main__":
    
    # Run the unit test
    # unittest.main()

    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"

    dataShare = DataShare()
    dataShare.config(configDir, instName=InstName.LSST)

    optCtrlDataDecorator = OptCtrlDataDecorator(dataShare)
    optCtrlDataDecorator.configOptCtrlData()

    optStateEstiDataDecorator = OptStateEstiDataDecorator(dataShare)
    optStateEstiDataDecorator.configOptStateEstiData()

    mixedData = OptCtrlDataDecorator(optStateEstiDataDecorator)
    mixedData.configOptCtrlData()

    testDataDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/tests/testData"
    testWfsFile = "lsst_wfs_error_iter0.z4c"
    testWfsFilePath = os.path.join(testDataDir, testWfsFile)

    sensorNameArray = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]
    wfErr, fieldIdx = mixedData.getWfAndFieldIdFromFile(testWfsFilePath, sensorNameArray)

    optStateEsti = OptStateEsti()
    optState = optStateEsti.estiOptState(mixedData, FilterType.REF, wfErr, fieldIdx)

    optCtrl = OptCtrl()
    state0InDof = mixedData.getState0FromFile()
    optCtrl.setState0(state0InDof)
    optCtrl.initStateToState0()
    optCtrl.setGain(1)

    # mixedData.xRef = "x00"
    uk = optCtrl.estiUk(mixedData, FilterType.REF, optState)

    print(uk)