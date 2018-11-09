import os
import unittest
import numpy as np

from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator
from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.OptCtrlDefault import OptCtrlDefault


if __name__ == "__main__":
    
    configDir = "/home/ttsai/Documents/github/ts_tcs_ofcPython/configData"

    dataShare = DataShare()
    dataShare.config(configDir, instName=InstName.LSST)

    optCtrlDataDecorator = OptCtrlDataDecorator(dataShare)
    optCtrlDataDecorator.configOptCtrlData()

    optCtrlDefault = OptCtrlDefault()