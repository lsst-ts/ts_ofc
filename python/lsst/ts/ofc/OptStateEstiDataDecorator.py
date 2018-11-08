import os
import numpy as np

from lsst.ts.ofc.Decorator import Decorator
from lsst.ts.ofc.Utility import FilterType, getMatchFilePath, getSetting, \
                                getDirFiles


class OptStateEstiDataDecorator(Decorator):

    def __init__(self, decoratedObj):
        """Initialization of optical state estimator data decorator class.

        Parameters
        ----------
        decoratedObj : obj
            Decorated object.
        """

        super(OptStateEstiDataDecorator, self).__init__(decoratedObj)

        self.wavelengthTable = None
        self.intrincZkFileName = None
        self.y2CorrectionFileName = None

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

        self.wavelengthTable = wavelengthTable
        self.intrincZkFileName = intrincZkFileName
        self.y2CorrectionFileName = y2CorrectionFileName

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

        filePath = os.path.join(self.getConfigDir(), self.wavelengthTable)
        param = filterType.name.lower()
        effWave = float(getSetting(filePath, param))

        return effWave

    def getY2Corr(self, fieldIdx, isNby1Array=False):
        """Get the y2 correction array. This is the zk offset between the
        camera center and corner.

        Parameters
        ----------
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        isNby1Array : bool, optional
            In the format of nx1 array or not. (the default is False.)

        Returns
        -------
        numpy.ndarray
            y2 correction array.
        """

        filePath = os.path.join(self.getInstDir(), self.y2CorrectionFileName)
        y2c = np.loadtxt(filePath)
        y2c = y2c[np.ix_(fieldIdx, self.getZn3Idx())]

        if (isNby1Array):
            y2c = y2c.reshape(-1, 1)

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
            Instrinsic zk of specific effective wavelength in um. The shape
            is nx1.
        """

        # Get the intrinsicZk file path
        reMatchStrTail = ""
        if (filterType != FilterType.REF):
            reMatchStrTail = "_" + filterType.name

        reMatchStr = "\A" + self.intrincZkFileName + reMatchStrTail + ".\S+"
        filePaths = getDirFiles(self.getInstDir())
        zkFilePath = getMatchFilePath(reMatchStr, filePaths)

        # Remap the zk index for z0-z2
        zkIdx = self.getZn3Idx() + 3

        # Get the intrinsicZk with the consideration of effective wavelength
        intrinsicZk = np.loadtxt(zkFilePath)
        intrinsicZk = intrinsicZk[np.ix_(fieldIdx, zkIdx)]
        intrinsicZk = intrinsicZk * self.getEffWave(filterType)
        intrinsicZk = intrinsicZk.reshape(-1, 1)

        return intrinsicZk


if __name__ == "__main__":
    pass
