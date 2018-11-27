import os
import numpy as np
from io import StringIO

from lsst.ts.ofc.Decorator import Decorator
from lsst.ts.ofc.Utility import FilterType, getMatchFilePath, getDirFiles
from lsst.ts.ofc.ParamReader import ParamReader


class OptStateEstiDataDecorator(Decorator):

    def __init__(self, decoratedObj):
        """Initialization of optical state estimator data decorator class.

        Parameters
        ----------
        decoratedObj : obj
            Decorated object.
        """

        super(OptStateEstiDataDecorator, self).__init__(decoratedObj)

        self._intrincZkFileName = None
        self._intrincZkFile = None
        self._wavelengthTable = None
        self._y2CorrectionFile = None

    def configOptStateEstiData(self, wavelengthTable="effWaveLength.txt",
                               intrincZkFileName="intrinsic_zn",
                               y2CorrectionFileName="y2.txt"):
        """Do the configuration of OptStateEstiDataDecorator class.

        Parameters
        ----------
        wavelengthTable : str, optional
            File name of effective wavelength for each filter in um. (the
            default is "effWaveLength.txt".)
        intrincZkFileName : str, optional
            Intric zk file name. (the default is "intrinsic_zn".)
        y2CorrectionFileName : str, optional
            y2 correction file name. (the default is "y2.txt".)
        """

        wavelengthTablePath = os.path.join(self.getConfigDir(),
                                           wavelengthTable)
        self._wavelengthTable = ParamReader(wavelengthTablePath)

        y2CorrectionFilePath = os.path.join(self.getInstDir(),
                                            y2CorrectionFileName)
        self._y2CorrectionFile = ParamReader(y2CorrectionFilePath)

        self._intrincZkFileName = intrincZkFileName

    def getEffWave(self, filterType):
        """Get the effective wavelength in um.

        This is based on the active filter type (U, G, R, I, Z, Y, REF). It
        is noted that "ref" means the monochromatic reference wavelength.

        Parameters
        ----------
        filterType : enum 'FilterType'
            Active filter type.

        Returns
        -------
        float
            Effective wavelength in um.
        """

        param = filterType.name.lower()
        effWave = float(self._wavelengthTable.getSetting(param))

        return effWave

    def getY2Corr(self, fieldIdx):
        """Get the y2 correction array. This is the zk offset between the
        camera center and corner.

        Parameters
        ----------
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        Returns
        -------
        numpy.ndarray
            y2 correction array.
        """

        content = self._y2CorrectionFile.getTxtContent()
        y2c = np.genfromtxt(StringIO(content), delimiter=" ")
        y2c = y2c[np.ix_(fieldIdx, self.getZn3Idx())]

        return y2c

    def getIntrinsicZk(self, filterType, fieldIdx):
        """Get the intrinsic zk of specific filter based on the array of
        field index.

        Parameters
        ----------
        filterType : enum 'FilterType'
            Active filter type.
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        Returns
        -------
        numpy.ndarray
            Instrinsic zk of specific effective wavelength in um.
        """

        # Get the intrinsicZk file path
        reMatchStrTail = ""
        if (filterType != FilterType.REF):
            reMatchStrTail = "_" + filterType.name

        reMatchStr = r"\A%s%s[.]\S+" % (self._intrincZkFileName,
                                        reMatchStrTail)
        filePaths = getDirFiles(self.getInstDir())
        zkFilePath = getMatchFilePath(reMatchStr, filePaths)

        # Remap the zk index for z0-z2
        zkIdx = self.getZn3Idx() + 3

        # Get the intrinsicZk with the consideration of effective wavelength
        self._intrincZkFile = ParamReader(zkFilePath)
        intrinsicZk = self._intrincZkFile.getMatContent()
        intrinsicZk = intrinsicZk[np.ix_(fieldIdx, zkIdx)]
        intrinsicZk = intrinsicZk * self.getEffWave(filterType)

        return intrinsicZk


if __name__ == "__main__":
    pass
