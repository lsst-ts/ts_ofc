import numpy as np
import unittest

from lsst.ts.ofc.CamRot import CamRot
from lsst.ts.ofc.Utility import DofGroup


if __name__ == "__main__":

    # # Run the unit test
    # unittest.main()
    
    camRot = CamRot()
    camRot.setRotAng(45)

    dofGroup = DofGroup.M2HexPos
    stateInDof = np.array([1, 2, 2, 4, 4])
    tiltXYinArcsec = (1224, 0)

    rotatedStateInDof = camRot.rotGroupDof(dofGroup, stateInDof, tiltXYinArcsec)
    print(rotatedStateInDof)

    stateInDof = np.zeros(20)
    stateInDof[0] = 1
    stateInDof[2] = 2
    tiltXYinArcsec = (0, 0)
    rotatedStateInDof = camRot.rotGroupDof(DofGroup.M2Bend, stateInDof, tiltXYinArcsec)
    print(rotatedStateInDof)
