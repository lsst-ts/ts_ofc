import os
import unittest
import numpy as np

from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator
from lsst.ts.ofc.Utility import InstName, FilterType

from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator


if __name__ == "__main__":
    
    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"

    dataShare = DataShare()
    dataShare.config(configDir, instName=InstName.LSST)

    optCtrlDataDecorator = OptCtrlDataDecorator(dataShare)
    optCtrlDataDecorator.configOptCtrlData()

    qWgt = optCtrlDataDecorator.getQwgtFromFile()
    pssnAlpha = optCtrlDataDecorator.getPssnAlphaFromFile()
    numQwgt = optCtrlDataDecorator.getNumOfFieldInQwgt()
    motRng = optCtrlDataDecorator.getMotRng()
    state0InDof = optCtrlDataDecorator.getState0FromFile()

    optStateEstiDataDecorator = OptStateEstiDataDecorator(dataShare)
    optStateEstiDataDecorator.configOptStateEstiData()

    mixedData = OptCtrlDataDecorator(optStateEstiDataDecorator)
    mixedData.configOptCtrlData()
    print(mixedData.getEffWave(FilterType.U))
