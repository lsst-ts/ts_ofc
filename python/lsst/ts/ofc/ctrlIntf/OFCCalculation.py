import numpy as np

from lsst.ts.wep.Utility import FilterType

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
    def __init__(self, fwhmToPssn):
        """Construct an OFC calculation. 

        This should be unique to an OFC algorithm / CCD.

        Parameters
        ----------
        fwhmToPssn : FWHMToPSSN
            The object used to convert FWHM values to PSSN values used
            by OFC.
        """
        super().__init__()
        self.fwhmToPssn = fwhmToPssn
        self.currentFilter = FilterType.REF

        self.pssnArray = np.array([])
        self.rotAngInDeg = 0.0

        self.gainByUser = -1

    def setFWHMSensorDataOfCam(self, listOfFWHMSensorData):
        """Set the list of FWHMSensorData of each CCD of camera. 

        Parameters
        ----------
        listOfFWHMSensorData : list [FWHMSensorData]
            List of FWHMSensorData which contains the sensor Id and FWHM data.
        """

        pssnList = []
        for aFWHMSensorData in listOfFWHMSensorData:
            sensorId = aFWHMSensorData.getSensorId()
            fwhm = aFWHMSensorData.getFwhmValues()

            # Need to transfrom the pssn array to effective pssn single value
            # by some way here
            pssn = self.fwhmToPssn.convertToPssn(fwhm)
            effectivePssn = np.average(pssn)
            pssnList.append(effectivePssn)

        self.pssnArray = np.array(pssnList)

    def setFilter(self, filterType):
        """Set the current filter.

        Parameters
        ----------
        filterType : FilterType
            The new filter configuration to use for OFC data processing.
        """

        self.currentFilter = filterType

    def getFilter(self):
        """Get the current filter.

        Returns
        -------
        FilterType
            The current filter configuration to use for OFC data processing.
        """

        return self.currentFilter

    def setRotAng(self, rotAngInDeg):
        """Set the camera rotation angle in degree.

        Parameters
        ----------
        rotAngInDeg : float
            The camera rotation angle in degree (-90 to 90).
        """

        self.rotAngInDeg = rotAngInDeg

    def getRotAng(self):
        """Get the camera rotation angle in degree.

        Returns
        -------
        float
            The camera rotation angle in degree.
        """

        return self.rotAngInDeg

    def resetOfcState(self):
        """Reset the OFC calculation state, which is the aggregated DOF now.

        This function is needed for the long slew angle of telescope.

        Returns
        -------
        CameraHexapodCorrection
            The position offset for the MT Hexapod.
        M2HexapodCorrection
            The position offset for the MT M2 Hexapod.
        M1M3Correction
            The figure offset for the MT M1M3.
        M2Correction
            The figure offset for the MT M2.
        """

        # I also need to clean OFC internal state data.
        camHexapodCorrection = CameraHexapodCorrection(0.0, 0.0, 0.0, 0.0, 0.0,
                                                    0.0)
        m2HexapodCorrection = M2HexapodCorrection(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        m1m3Correction = M1M3Correction([0.0] * 156)
        m2Correction = M2Correction([0.0] * 72)

        return camHexapodCorrection, m2HexapodCorrection, m1m3Correction, \
               m2Correction

    def setGainByUser(self, gainByUser=-1):
        """Set the gain value by the user.

        Parameters
        ----------
        gainByUser : float, optional
            The gain value by the user. This value should be in (0, 1). The
            default value is -1, which means the gain value will be decided by
            the PSSN, which comes from the FWHM by DM team. (the default is -1.) 
        """

        self.gainByUser = gainByUser

    def setGainByPSSN(self):
        """Set the gain value based on the PSSN, which comes from the FWHM by
        DM team.."""

        self.setGainByUser(gainByUser=-1)

    def calculateCorrections(self, listOfWfErr):
        """Calculate the Hexapod, M1M3, and M2 corrections from the FWHM
        and wavefront error.

        Parameters
        ----------
        listOfWfErr : list [SensorWavefrontError]
            The list of wavefront error of each sensor for an exposure.

        Returns
        -------
        CameraHexapodCorrection
            The position offset for the MT Hexapod.
        M2HexapodCorrection
            The position offset for the MT M2 Hexapod.
        M1M3Correction
            The figure offset for the MT M1M3.
        M2Correction
            The figure offset for the MT M2.
        """

        camHexapodCorrection = CameraHexapodCorrection(0.0, 0.0, 0.0, 0.0, 0.0,
                                                       0.0)
        m2HexapodCorrection = M2HexapodCorrection(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        m1m3Correction = M1M3Correction([0.0] * 156)
        m2Correction = M2Correction([0.0] * 72)

        return camHexapodCorrection, m2HexapodCorrection, m1m3Correction, \
               m2Correction


if __name__ == "__main__":
    pass
