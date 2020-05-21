from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfLsst import OFCCalculationOfLsst
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfComCam import OFCCalculationOfComCam
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfSh import OFCCalculationOfSh
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfCmos import OFCCalculationOfCmos


class OFCCalculationFactory(object):
    """Factory for creating the correct OFC calculation based off the
    instrument currently being used.
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def getCalculator(instName, state0Dof=None):
        """Get a calculator to process wavefront error.

        Parameters
        ----------
        instName : enum 'InstName'
            The instrument to get the wavefront calculator for.
        state0Dof : dict, optional
            State 0 DoF dictionary. If None (=default), the instrument's
            default will be used. See
            :lsst:ts:ofc:`OptCtrlDataDecorator.getState0FromDict` for format
            details.

        Returns
        -------
        OFCCalculationOfLsst, OFCCalculationOfComCam, OFCCalculationOfSh, or
        OFCCalculationOfCmos
            Concrete child class of OFCCalculation class.

        Raises
        ------
        ValueError
            This instrument is not supported.
        """

        if (instName == InstName.LSST):
            return OFCCalculationOfLsst(state0Dof)
        elif (instName == InstName.COMCAM):
            return OFCCalculationOfComCam(state0Dof)
        elif (instName == InstName.SH):
            return OFCCalculationOfSh(state0Dof)
        elif (instName == InstName.CMOS):
            return OFCCalculationOfCmos(state0Dof)
        else:
            raise ValueError("This instrument is not supported.")


if __name__ == "__main__":
    pass
