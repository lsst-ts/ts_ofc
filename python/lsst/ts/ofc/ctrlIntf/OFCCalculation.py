import numpy as np

from lsst.ts.wep.Utility import FilterType

from lsst.ts.ofc.Utility import getConfigDir, DofGroup
from lsst.ts.ofc.DataShare import DataShare
from lsst.ts.ofc.OptStateEstiDataDecorator import OptStateEstiDataDecorator
from lsst.ts.ofc.OptCtrlDataDecorator import OptCtrlDataDecorator
from lsst.ts.ofc.OptStateEsti import OptStateEsti
from lsst.ts.ofc.OptCtrl import OptCtrl
from lsst.ts.ofc.ZTAAC import ZTAAC
from lsst.ts.ofc.CamRot import CamRot
from lsst.ts.ofc.BendModeToForce import BendModeToForce
from lsst.ts.ofc.SubSysAdap import SubSysAdap

from lsst.ts.ofc.ctrlIntf.CameraHexapodCorrection import CameraHexapodCorrection
from lsst.ts.ofc.ctrlIntf.M2HexapodCorrection import M2HexapodCorrection
from lsst.ts.ofc.ctrlIntf.M1M3Correction import M1M3Correction
from lsst.ts.ofc.ctrlIntf.M2Correction import M2Correction


class OFCCalculation(object):
    """Base class for converting wave front errors into corrections
    utilized by M1M3 (figure), M2 (position and figure), and Hexapod
    (position).

    There will be different implementations of this for different
    types of CCDs (normal, full array mode, comcam, cmos, shwfs).
    """
    def __init__(self, fwhmToPssn, instName,
                 m1m3BendModeFileName="M1M3_1um_156_force.yaml",
                 m2BendModeFileName="M2_1um_force.yaml"):
        """Construct an OFC calculation.

        This should be unique to an OFC algorithm / CCD.

        FWHM: Full width at half maximum.
        PSSN: Normalized point source sensitivity.

        Parameters
        ----------
        fwhmToPssn : FWHMToPSSN
            The object used to convert FWHM values to PSSN values used by OFC.
        instName : enum 'InstName'
            Instrument name.
        m1m3BendModeFileName : str, optional
            M1M3 bending mode file name. (the default is
            "M1M3_1um_156_force.yaml".)
        m2BendModeFileName : str, optional
            M2 bending mode file name. (the default is "M2_1um_force.yaml".)
        """

        self.fwhmToPssn = fwhmToPssn
        self.pssnData = {"sensorId": np.array([], dtype=int),
                         "pssn": np.array([])}

        self.useGainByPssn = True

        self.camRot = CamRot(rotAngInDeg=0.0)

        configDir = getConfigDir()
        self.ztaac = self._configZTAAC(configDir, instName)

        self.m1m3BendModeToForce = self._configBendingModeToForce(
            configDir, DofGroup.M1M3Bend, m1m3BendModeFileName)
        self.m2BendModeToForce = self._configBendingModeToForce(
            configDir, DofGroup.M2Bend, m2BendModeFileName)

        self.subSysAdap = self._configSubSysAdap(configDir)

        self.dofFromLastVisit = np.array([])
        self._initDofFromLastVisit()

    def _configZTAAC(self, configDir, instName):
        """Configurate the ZTAAC.

        ZTAAC: Zernike to actuator adjustment calculator.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        instName : enum 'InstName'
            Instrument name.

        Returns
        -------
        ZTAAC
            Configurated ZTAAC object.
        """

        # Prepare the data object for the ZTAAC to use
        dataShare = DataShare()
        dataShare.config(configDir, instName=instName)

        optStateEstiData = OptStateEstiDataDecorator(dataShare)
        optStateEstiData.configOptStateEstiData()

        mixedData = OptCtrlDataDecorator(optStateEstiData)
        mixedData.configOptCtrlData()

        # Instantiate the ZTAAC object with the configured objects
        ztaac = ZTAAC(OptStateEsti(), OptCtrl(), mixedData)

        # Set the state 0 and state
        ztaac.setState0FromFile()
        ztaac.setStateToState0()

        # Configure the parameters
        ztaac.config(filterType=FilterType.REF)

        return ztaac

    def _configBendingModeToForce(self, configDir, dofGroup,
                                  bendingModeFileName):
        """Configurate the bending mode to force.

        DOF: Degree of freedom.

        Parameters
        ----------
        configDir : str
            Configuration directory.
        dofGroup : enum 'DofGroup'
            DOF group.
        bendingModeFileName : str
            Bending mode file name.

        Returns
        -------
        BendModeToForce
            Configurated BendModeToForce object.
        """

        bendModeToForce = BendModeToForce()
        bendModeToForce.config(configDir, dofGroup, bendingModeFileName)

        return bendModeToForce

    def _configSubSysAdap(self, configDir):
        """Configurate the subsystem adaptor.

        Parameters
        ----------
        configDir : str
            Configuration directory.

        Returns
        -------
        SubSysAdap
            Configurated SubSysAdap object.
        """

        subSysAdap = SubSysAdap()
        subSysAdap.config(configDir)

        return subSysAdap

    def _initDofFromLastVisit(self):
        """Initialize the DOF correction from the last visit.

        DOF: Degree of freedom.
        """

        numOfState0 = self.ztaac.optCtrl.getNumOfState0()
        self.dofFromLastVisit = np.zeros(numOfState0)

    def getZtaac(self):
        """Get the ZTAAC.

        ZTAAC: Zernike to actuator adjustment calculator.

        Returns
        -------
        lsst.ts.ofc.ZTAAC
            ZTAAC object.
        """

        return self.ztaac

    def getPssnData(self):
        """Get the PSSN data.

        PSSN: Normalized point source sensitivity.

        Returns
        -------
        dict
            PSSN data.
        """

        return self.pssnData

    def setFWHMSensorDataOfCam(self, listOfFWHMSensorData):
        """Set the list of FWHMSensorData of each CCD of camera.

        Parameters
        ----------
        listOfFWHMSensorData : list [FWHMSensorData]
            List of FWHMSensorData which contains the sensor Id and FWHM data.
        """

        sensorId = np.array([], dtype=int)
        pssn = np.array([])
        for aFWHMSensorData in listOfFWHMSensorData:

            sensorId = np.append(sensorId, aFWHMSensorData.getSensorId())

            fwhm = aFWHMSensorData.getFwhmValues()
            pssnOfSensor = self.fwhmToPssn.convertToPssn(fwhm)
            effPssn = self._getEffPssn(pssnOfSensor)
            pssn = np.append(pssn, effPssn)

        self.pssnData["sensorId"] = sensorId
        self.pssnData["pssn"] = pssn

    def _getEffPssn(self, pssnOfSensor):
        """Get the effective PSSN of single sensor.

        PSSN: Normalized point source sensitivity.

        Parameters
        ----------
        pssnOfSensor : numpy.ndarray
            PSSN of sensor as an array.

        Returns
        -------
        float
            Effective PSSN of single sensor.
        """

        # Use the average here. But need to have a better algorithm in a latter
        # time.
        effPssn = np.average(pssnOfSensor)

        return effPssn

    def setFilter(self, filterType):
        """Set the current filter.

        Parameters
        ----------
        filterType : enum 'FilterType'
            The new filter configuration to use for OFC data processing.
        """

        self.ztaac.setFilter(filterType)

    def getFilter(self):
        """Get the current filter.

        Returns
        -------
        enum 'FilterType'
            The current filter configuration to use for OFC data processing.
        """

        return self.ztaac.getFilter()

    def setRotAng(self, rotAngInDeg):
        """Set the camera rotation angle in degree.

        Parameters
        ----------
        rotAngInDeg : float
            The camera rotation angle in degree (-90 to 90).
        """

        self.camRot.setRotAng(rotAngInDeg)

    def getRotAng(self):
        """Get the camera rotation angle in degree.

        Returns
        -------
        float
            The camera rotation angle in degree.
        """

        return self.camRot.getRotAng()

    def resetOfcState(self):
        """Reset the OFC calculation state, which is the aggregated DOF now.

        This function is needed for the long slew angle of telescope.

        DOF: Degree of freedom.

        Returns
        -------e
        M2HexapodCorrection
            The position offset for the MT M2 Hexapod.
        CameraHexapodCorrection
            The position offset for the MT Hexapod.
        M1M3Correction
            The figure offset for the MT M1M3.
        M2Correction
            The figure offset for the MT M2.
        """

        self.ztaac.setStateToState0()
        self._initDofFromLastVisit()

        return self._getSubSysCorr()

    def _getSubSysCorr(self):
        """Get the subsystem correction.

        Returns
        -------
        M2HexapodCorrection
            The position offset for the MT M2 Hexapod.
        CameraHexapodCorrection
            The position offset for the MT Hexapod.
        M1M3Correction
            The figure offset for the MT M1M3.
        M2Correction
            The figure offset for the MT M2.
        """

        m2HexapodCorrection = self._getHexCorr(DofGroup.M2HexPos)
        camHexapodCorrection = self._getHexCorr(DofGroup.CamHexPos)

        m1m3Correction = self._getMirrorActForceCorr(DofGroup.M1M3Bend)
        m2Correction = self._getMirrorActForceCorr(DofGroup.M2Bend)

        return m2HexapodCorrection, camHexapodCorrection, m1m3Correction, \
            m2Correction

    def _getHexCorr(self, dofGroup):
        """Get the hexapod correction.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group (M2HexPos or CamHexPos).

        Returns
        -------
        M2HexapodCorrection or CameraHexapodCorrection
            Hexapod correction.
        """

        self._checkDofGroupIsHexpod(dofGroup)

        hexDof = self.ztaac.getGroupDof(dofGroup)
        transHexDof = self.subSysAdap.transHexaPosToSubSys(hexDof)
        x, y, z, rx, ry, rz = transHexDof

        if (dofGroup == DofGroup.M2HexPos):
            hexCorr = M2HexapodCorrection(x, y, z, rx, ry, w=rz)
        elif (dofGroup == DofGroup.CamHexPos):
            hexCorr = CameraHexapodCorrection(x, y, z, rx, ry, w=rz)

        return hexCorr

    def _checkDofGroupIsHexpod(self, dofGroup):
        """Check the input DOF group is hexapod.

        DOF: Degree of freedom.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group (M2HexPos or CamHexPos).

        Raises
        ------
        ValueError
            The input DOF group is not hexapod.
        """

        if dofGroup not in (DofGroup.M2HexPos, DofGroup.CamHexPos):
            raise ValueError("The input DOF group (%s) is not hexapod."
                             % dofGroup)

    def _getMirrorActForceCorr(self, dofGroup):
        """Get the mirror actuator forces correction.

        Parameters
        ----------
        dofGroup : enum 'DofGroup'
            DOF group (M1M3Bend or M2Bend).

        Returns
        -------
        M1M3Correction or M2Correction
            Mirror actuator forces correction.
        """

        BendModeToForce.checkDofGroupIsMirror(dofGroup)

        # Get the DOF of mirror
        mirrorDof = self.ztaac.getGroupDof(dofGroup)

        # Transform the DOF to actuator forces
        if (dofGroup == DofGroup.M1M3Bend):
            actForce = self.m1m3BendModeToForce.calcActForce(mirrorDof)
        elif (dofGroup == DofGroup.M2Bend):
            actForce = self.m2BendModeToForce.calcActForce(mirrorDof)

        # Transform the actuator forces to the subsystem's coordinate
        # from ZEMAX coordinate
        transActForce = self.subSysAdap.transActForceToSubSys(dofGroup,
                                                              actForce)

        # Truncate the M2 actuator force
        # We do this is just because we use the M1M3 bending mode file (156
        # actuators) to mimic the M2 bending mode file (72 actuators) at this
        # moment.
        if (dofGroup == DofGroup.M2Bend):
            transActForce = transActForce[0: M2Correction.NUM_OF_ACT]

        # Instantiate the correction object
        if (dofGroup == DofGroup.M1M3Bend):
            mirrorCorr = M1M3Correction(transActForce)
        elif (dofGroup == DofGroup.M2Bend):
            mirrorCorr = M2Correction(transActForce)

        return mirrorCorr

    def setGainByUser(self, gainByUser=-1):
        """Set the gain value by the user.

        Parameters
        ----------
        gainByUser : float, optional
            The gain value by the user. This value should be in (0, 1). The
            default value is -1, which means the gain value will be decided by
            the PSSN, which comes from the FWHM by DM team. (the default is
            -1.).
        """

        if (gainByUser == -1):
            self.useGainByPssn = True
        else:
            try:
                self.ztaac.setGain(gainByUser)
                self.useGainByPssn = False
            except Exception:
                raise

    def setGainByPSSN(self):
        """Set the gain value based on the PSSN, which comes from the FWHM by
        DM team.."""

        self.useGainByPssn = True

    def getGainInUse(self):
        """Get the gain value in use now.

        Returns
        -------
        float
            Gain value.
        """

        return self.ztaac.getGainInUse()

    def calculateCorrections(self, listOfWfErr):
        """Calculate the Hexapod, M1M3, and M2 corrections from the FWHM
        and wavefront error.

        Parameters
        ----------
        listOfWfErr : list [lsst.ts.wep.ctrlIntf.SensorWavefrontError]
            The list of wavefront error of each sensor for an exposure.

        Returns
        -------
        M2HexapodCorrection
            The position offset for the MT M2 Hexapod.
        CameraHexapodCorrection
            The position offset for the MT Hexapod.
        M1M3Correction
            The figure offset for the MT M1M3.
        M2Correction
            The figure offset for the MT M2.
        """

        # Set the gain value
        if (self.useGainByPssn):
            self._setZtaacGainByPSSN()

        # Collect the wavefront error and sensor name
        numOfZk = listOfWfErr[0].getNumOfZk()
        wfZkData = np.empty((0, numOfZk))
        sensorIdList = []
        for wfErr in listOfWfErr:
            sensorId = wfErr.getSensorId()
            sensorIdList.append(sensorId)

            annularZernikePoly = wfErr.getAnnularZernikePoly()
            wfZkData = np.vstack((wfZkData, annularZernikePoly))

        sensorNameList = self.ztaac.mapSensorIdToName(sensorIdList)[0]

        # Calculate the uk based on the control algorithm
        uk = self.ztaac.estiUkWithGain(wfZkData, sensorNameList)

        # Consider the camera rotation
        rotUk = self.ztaac.rotUk(self.camRot, uk)

        # Assign the value to the last visit DOF
        self._setStateCorrectionFromLastVisit(rotUk)

        # Aggregate the rotated uk
        self.ztaac.aggState(rotUk)

        return self._getSubSysCorr()

    def _setZtaacGainByPSSN(self):
        """Set the ZTAAC gain value by PSSN.

        ZTAAC: Zernike to actuator adjustment calculator.
        PSSN: Normalized point source sensitivity.
        """

        pssn = self.pssnData["pssn"]

        sensorId = self.pssnData["sensorId"]
        sensorNameList = self.ztaac.mapSensorIdToName(sensorId.tolist())[0]

        self.ztaac.setGainByPSSN(pssn, sensorNameList)

    def _setStateCorrectionFromLastVisit(self, calcDof):
        """Set the state (or degree of freedom, DOF) correction from the last
        visit.

        Parameters
        ----------
        calcDof : numpy.ndarray
            Calculated DOF.
        """

        numOfState0 = self.ztaac.optCtrl.getNumOfState0()
        dofFromLastVisit = np.zeros(numOfState0)

        dofIdx = self.ztaac.dataShare.getDofIdx()
        dofFromLastVisit[dofIdx] = calcDof

        self.dofFromLastVisit = dofFromLastVisit

    def getStateCorrectionFromLastVisit(self):
        """Get the state (or degree of freedom, DOF) correction from the last
        visit.

        The default output units are:
        1. M2 hexapod position (dz in um, dx in um, dy in um, rx in arcsec,
        ry in arcsec).
        2. Cam hexapod position (dz in um, dx in um, dy in um, rx in arcsec,
        ry in arcsec).
        3. M1M3 20 bending mode in um.
        4. M2 20 bending mode in um.

        Returns
        -------
        numpy.ndarray
            State (or DOF) correction from the last visit.
        """

        return self.dofFromLastVisit

    def getStateAggregated(self):
        """Get the aggregated state (or degree of freedom, DOF).

        The default output units are:
        1. M2 hexapod position (dz in um, dx in um, dy in um, rx in arcsec,
        ry in arcsec).
        2. Cam hexapod position (dz in um, dx in um, dy in um, rx in arcsec,
        ry in arcsec).
        3. M1M3 20 bending mode in um.
        4. M2 20 bending mode in um.

        Returns
        -------
        numpy.ndarray
            Aggregated state (or DOF).
        """

        stateAgg = np.array([])
        for dofGroup in DofGroup:
            dof = self.ztaac.getGroupDof(dofGroup)
            stateAgg = np.append(stateAgg, dof)

        return stateAgg


if __name__ == "__main__":
    pass
