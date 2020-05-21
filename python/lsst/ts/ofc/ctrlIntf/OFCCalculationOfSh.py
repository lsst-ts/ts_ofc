from lsst.ts.ofc.Utility import InstName
from lsst.ts.ofc.ctrlIntf.OFCCalculationOfIota import OFCCalculationOfIota


class OFCCalculationOfSh(OFCCalculationOfIota):
    """The concrete child class of OFCCalculation of the Shack-Hartmann"""

    def __init__(self, state0Dof=None):
        """Construct an OFC calculation of S.H. camera.

        Parameters
        ----------
        state0Dof : dict, optional
            State 0 DoF dictionary. If None (=default), the instrument's
            default will be used. See
            :lsst:ts:ofc:`OptCtrlDataDecorator.getState0FromDict` for format
            details.

        S.H.: Shack-Hartmann.
        """

        # Use the data in ComCam
        super(OFCCalculationOfSh, self).__init__(InstName.COMCAM, "sh", state0Dof)


if __name__ == "__main__":
    pass
