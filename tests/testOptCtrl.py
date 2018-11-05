import os
import numpy as np
import unittest

from lsst.ts.ofc.OptStateEsti import InstName, FilterType
from lsst.ts.ofc.OptStateEsti import OptStateEsti
from lsst.ts.ofc.OptCtrl import OptCtrl


if __name__ == "__main__":
    
    # Run the unit test
    unittest.main()

    # configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"
    # optCtrl = OptCtrl()
    # optCtrl.config(configDir, instName=InstName.LSST,
    #                configFileName="optiPSSN_x00.ctrl")
    # optCtrl.setGain(1)

    # # dofIdx = [2,3,4,5]
    # # calcDof = [0.1, 0.2, 0.3, 0.4]
    # # optCtrl.aggState(calcDof, dofIdx)
    # # print(optCtrl.getState(dofIdx))

    # dofFilePath = "/home/ttsai/Documents/github/ts_tcs_ofcPython/tests/testData/lsst_pert_iter1.txt"
    # dof = optCtrl.getDofFromFile(dofFilePath)

    # optStateEsti = OptStateEsti()
    # optStateEsti.config(configDir, instName=InstName.LSST)

    # effWave = 0.5
    # senM = optStateEsti.senM
    # dofIdx = optStateEsti.dofIdx
    # zn3Idx = optStateEsti.zn3Idx
    # optCtrl.setMatF(zn3Idx, dofIdx, effWave, senM)
    
    # # pssn = np.ones(31)*0.96
    # # fieldIdx = np.arange(31)
    # # fwhmGq = optCtrl.calcEffGQFWHM(pssn, fieldIdx)
    
    # # motRng = optCtrl.getMotRng()

    # testDataDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/tests/testData"
    # testWfsFile = "lsst_wfs_error_iter0.z4c"
    # testWfsFilePath = os.path.join(testDataDir, testWfsFile)
    # sensorNameArray = ["R44_S00", "R04_S20", "R00_S22", "R40_S02"]

    # wfErr, fieldIdx = optStateEsti.getWfAndFieldIdFromFile(testWfsFilePath, sensorNameArray)
    # optStateEsti.setAandPinvA(fieldIdx)
    # optSt = optStateEsti.estiOptState(FilterType.REF, wfErr, fieldIdx)

    # fieldNumInQwgt = optCtrl.getNumOfFieldInQwgt()
    # y2c = optStateEsti.getY2Corr(np.arange(fieldNumInQwgt), isNby1Array=False)    
    # uk = optCtrl.estiUk(zn3Idx, dofIdx, effWave, senM, y2c, optSt)
    # print(uk)