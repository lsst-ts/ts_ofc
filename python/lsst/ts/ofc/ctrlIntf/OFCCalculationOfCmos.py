from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfIota import OFCCalculationOfIota


class OFCCalculationOfCmos(OFCCalculationOfIota):
    """The concrete child class of OFCCalculation of the CMOS"""

    def __init__(self, state0Dof=None):
        """Construct an OFC calculation of CMOS camera.

        Parameters
        ----------
        state0Dof : dict, optional
            State 0 DoF dictionary. If None (=default), the instrument's
            default will be used. See
            :lsst:ts:ofc:`OptCtrlDataDecorator.getState0FromDict` for format
            details.

        CMOS: Complementary metal–oxide–semiconductor.
        """

        # Use the data in ComCam
        super(OFCCalculationOfCmos, self).__init__(InstName.COMCAM, "cmos", state0Dof)


if __name__ == "__main__":
    pass
