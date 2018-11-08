import os
import unittest
import numpy as np

from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator
from lsst.ts.ofc.Utility import InstName, FilterType, DofGroup


if __name__ == "__main__":
    
    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"

    dataShare = DataShare()
    dataShare.config(configDir, instName=InstName.LSST)

    optStateEstiData = OptStateEstiDataDecorator(dataShare)
    optStateEstiData.configOptStateEstiData()

    effWave = optStateEstiData.getEffWave(FilterType.REF)

    fieldIdx = optStateEstiData.getFieldIdx(["R22_S11", "R22_S12"])
    y2c = optStateEstiData.getY2Corr(fieldIdx, isNby1Array=True)
    intrinsicZk = optStateEstiData.getIntrinsicZk(FilterType.REF, fieldIdx)