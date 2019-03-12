import os
import numpy as np

from lsst.ts.wep.Utility import FilterType

from lsst.ts.ofc.Decorator import Decorator
from lsst.ts.ofc.Utility import getMatchFilePath, getDirFiles
from lsst.ts.ofc.ParamReaderYaml import ParamReaderYaml


class OptStateEstiDataDecorator(Decorator):

    ZN3_IDX_IN_INTRINSIC_ZN_FILE = 3

    def __init__(self, decoratedObj):
        """Initialization of optical state estimator data decorator class.

        Parameters
        ----------
        decoratedObj : obj
            Decorated object.
        """

        super(OptStateEstiDataDecorator, self).__init__(decoratedObj)

        self._wavelengthTable = ParamReaderYaml()
        self._intrincZkFileName = ""
        self._intrincZkFile = ParamReaderYaml()
        self._y2CorrectionFile = ParamReaderYaml()

    def configOptStateEstiData(self, wavelengthTable="effWaveLength.yaml",
                               intrincZkFileName="intrinsicZn",
                               y2CorrectionFileName="y2.yaml"):
        """Do the configuration of OptStateEstiDataDecorator class.

        Parameters
        ----------
        wavelengthTable : str, optional
            File name of effective wavelength for each filter in um. (the
            default is "effWaveLength.yaml".)
        intrincZkFileName : str, optional
            Intric zk file name. (the default is "intrinsicZn".)
        y2CorrectionFileName : str, optional
            y2 correction file name. (the default is "y2.yaml".)
        """

        wavelengthTablePath = os.path.join(self.getConfigDir(),
                                           wavelengthTable)
        self._wavelengthTable.setFilePath(wavelengthTablePath)

        y2CorrectionFilePath = os.path.join(self.getInstDir(),
                                            y2CorrectionFileName)
        self._y2CorrectionFile.setFilePath(y2CorrectionFilePath)

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

        y2c = self._y2CorrectionFile.getMatContent()
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
        if (filterType == FilterType.REF):
            reMatchStrTail = ""
        else:
            reMatchStrTail = filterType.name

        reMatchStr = r"\A%s%s[.]\S+" % (self._intrincZkFileName,
                                        reMatchStrTail)
        filePaths = getDirFiles(self.getInstDir())
        zkFilePath = getMatchFilePath(reMatchStr, filePaths)

        # Remap the zk index for z0-z2
        zkIdx = self.getZn3Idx() + self.ZN3_IDX_IN_INTRINSIC_ZN_FILE

        # Get the intrinsicZk with the consideration of effective wavelength
        self._intrincZkFile.setFilePath(zkFilePath)
        intrinsicZk = self._intrincZkFile.getMatContent()
        intrinsicZk = intrinsicZk[np.ix_(fieldIdx, zkIdx)]
        intrinsicZk = intrinsicZk * self.getEffWave(filterType)

        return intrinsicZk


if __name__ == "__main__":
    pass
