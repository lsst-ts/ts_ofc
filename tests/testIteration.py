import os
import numpy as np
import unittest

from lsst.ts.ofc.Utility import InstName, FilterType, DofGroup, getModulePath
from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator
from lsst.ts.ofc.OptStateEsti import OptStateEsti
from lsst.ts.ofc.OptCtrl import OptCtrl
from lsst.ts.ofc.ZTAAC import ZTAAC
from lsst.ts.ofc.CamRot import CamRot
from lsst.ts.ofc.IterDataReader import IterDataReader


class TestIteration(unittest.TestCase):
    """Test the iteration."""

    def setUp(self):

        # Set up the object of data share class. This contains the
        # information of indexes of zk and degree of freedom (DOF)
        # to use.
        dataShare = DataShare()
        configDir = os.path.join(getModulePath(), "configData")
        dataShare.config(configDir, instName=InstName.LSST)

        # Decorate the DataShare object to get the data needed
        # for the OptStateEsti object.
        optStateEstiData = OptStateEstiDataDecorator(dataShare)
        optStateEstiData.configOptStateEstiData()

        # Decorate the DataShare object to get the data needed
        # for the OptCtrl object.
        mixedData = OptCtrlDataDecorator(optStateEstiData)
        mixedData.configOptCtrlData(configFileName="optiPSSN_x00.ctrl")

        # Instantiate the objects of OptStateEsti and OptCtrl classes.
        optStateEsti = OptStateEsti()
        optCtrl = OptCtrl()

        # Instantiate the ZTAAC object with the configured objects.
        self.ztaac = ZTAAC(optStateEsti, optCtrl, mixedData)

        # Do the configuration of ZTAAC object.
        self.ztaac.config(filterType=FilterType.REF, defaultGain=0.7,
                          fwhmThresholdInArcsec=0.2)

        # Set the state 0 from file. This is only used in the simulation.
        # In the real control, the state 0 should come from the subsystem
        # by SAL (software abstracion layer). But the algorithm for this
        # needs to be developed.
        self.ztaac.setState0FromFile(state0InDofFileName="state0inDof.txt")

        # Initialize the state to state 0.
        self.ztaac.setStateToState0()

        # Instantiate the camera rotation object.
        self.camRot = CamRot()

        # Set up the rotation angle.
        # The angle is zero degree in the test data.
        self.camRot.setRotAng(0)

        # Read the test iteration data by the IM closed-loop simulation.
        iterDataDir = os.path.join(getModulePath(), "tests", "testData",
                                   "iteration")
        self.iterDataReader = IterDataReader(iterDataDir)

    def testIteration(self):

        # Read the wavefront sensor Id in the test data.
        # It is noted that the sensor Id will be used instead of sensor
        # name in the SAL communication in the contrl mode.
        sensorIdList = self.iterDataReader.getWfsSensorIdList()

        # Map the sensor Id (e.g. 0, 1, etc.) to sensor name (such as "R22_S11").
        sensorNameList = self.ztaac.mapSensorIdToName(sensorIdList)[0]

        # Map the sensor Id to sensor name for the PSSN data.
        # PSSN is the normalized point source sensitivity.
        # In the control mode, DM team will provide the image quality (FWHM)
        # for each sensor. T&S team will transform the FWHM to PSSN.
        # FWHM is the full-width at half maximum.
        pssnIdList = self.iterDataReader.getPssnSensorIdList()
        pssnSensorNameList = self.ztaac.mapSensorIdToName(pssnIdList)[0]

        # Run the iteration for five times.
        maxIterNum = 5
        for iterNum in range(0, maxIterNum):

            # Read the PSSN data in the specific iteration.
            pssn = self.iterDataReader.getPssn(iterNum)

            # Decide the gain value based on the PSSN data.
            self.ztaac.setGainByPSSN(pssn, pssnSensorNameList)

            # Read the wavefront error data in the specific iteration. 
            wfErr = self.iterDataReader.getWfsErr(iterNum)

            # Calculate the uk based on the control algorithm.
            uk = self.ztaac.estiUkWithGain(wfErr, sensorNameList)

            # Consider the camera rotation.
            rotUk = self.ztaac.rotUk(self.camRot, uk)

            # Aggregate the rotated uk.
            self.ztaac.aggState(rotUk)

            # Collect the DOF for the comparison
            dof = []
            for dofGroup in DofGroup:
                # Get the DOF for each group
                dofOfGroup = self.ztaac.getGroupDof(dofGroup)
                dof = np.append(dof, dofOfGroup)

            # In the simulation mode, the PhoSim needs the total state
            # of telescope to do the perturbation. In the control mode,
            # only the aggregated totatl state (state - state0) is needed.
            dof += self.ztaac.getState0()

            # Read the answer of DOF in the test file. The calculated DOF
            # is applied to the next iteration/ visit. This is why we read
            # the data in "iterNum + 1" instead of "iterNum".
            dofAns = self.iterDataReader.getDof(iterNum + 1)

            # Compare the DOF with answer.
            delta = np.sum(np.abs(dof - dofAns))
            self.assertLess(delta, 0.002)


if __name__ == "__main__":

    # Run the unit test
    unittest.main()
