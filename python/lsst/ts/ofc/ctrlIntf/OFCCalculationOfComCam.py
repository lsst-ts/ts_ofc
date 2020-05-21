from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculation import OFCCalculation
from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN


class OFCCalculationOfComCam(OFCCalculation):
    """The concrete child class of OFCCalculation of the ComCam"""

    def __init__(self, state0Dof=None):
        """Construct an OFC calculation of ComCam.

        Parameters
        ----------
        state0Dof : dict, optional
            State 0 DoF dictionary. If None (=default), the instrument's
            default will be used. See
            :lsst:ts:ofc:`OptCtrlDataDecorator.getState0FromDict` for format
            details.

        ComCam: Commissioning camera.
        """
        super(OFCCalculationOfComCam, self).__init__(FWHMToPSSN(),
                                                     InstName.COMCAM,
                                                     state0Dof)


if __name__ == "__main__":
    pass
