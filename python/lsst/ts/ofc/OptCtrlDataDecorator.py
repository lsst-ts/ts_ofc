from lsst.ts.ofc.Decorator import Decorator


class OptCtrlDataDecorator(object):

    def __init__(self, decoratedObj):
        """Initialization of optimal control data decorator class.

        Parameters
        ----------
        decoratedObj : obj
            Decorated object.
        """

        super(OptCtrlDataDecorator, self).__init__()

        self.rigidBodyStrokeFileName = None
        self.weightingFileName = None
        self.pssnAlphaFileName = None

        self.strategy = None
        self.xRef = None
        self.penality = {"M1M3Act": 0, "M2Act": 0, "Motion": 0}



if __name__ == "__main__":
    pass