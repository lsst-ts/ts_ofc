import os
import unittest

from lsst.ts.ofc.Utility import InstName, FilterType
from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEsti import OptStateEsti


if __name__ == "__main__":
    
    # Run the unit test
    # unittest.main()

    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"

    dataShare = DataShare()
    dataShare.config(configDir, instName=InstName.LSST)

    testDataDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/tests/testData"
    testWfsFile = "lsst_wfs_error_iter0.z4c"
    testWfsFilePath = os.path.join(testDataDir, testWfsFile)

    sensorNameArray = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]
    wfErr, fieldIdx = dataShare.getWfAndFieldIdFromFile(testWfsFilePath, sensorNameArray)

    optStateEsti = OptStateEsti()
    optState = optStateEsti.estiOptState(dataShare, FilterType.REF, wfErr, fieldIdx)
    print(optState)