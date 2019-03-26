import os

from lsst.ts.ofc.ctrlIntf.OFCCalculation import OFCCalculation
from lsst.ts.ofc.ctrlIntf.FWHMToPSSN import FWHMToPSSN


class OFCCalculationOfIota(OFCCalculation):
    """The concrete child class of OFCCalculation of IOTA."""

    def __init__(self, instName, specificInstDirName):
        """Construct an OFC calculation of IOTA.

        IOTA: Initial optical test assembly.

        Parameters
        ----------
        instName : enum 'InstName'
            Instrument name.
        specificInstDirName : str
            Specific instrument directory name.
        """

        super(OFCCalculationOfIota, self).__init__(FWHMToPSSN(), instName)

        # Set the idx of zk and DOF
        self._setZkAndDofIdxOfIota(specificInstDirName, instName)

    def _setZkAndDofIdxOfIota(self, specificInstDirName, instName):
        """Set the Z3-Zn and DOF indexes of specific IOTA camera.

        DOF: degree of freedom.
        IOTA: Initial optical test assembly.

        Parameters
        ----------
        specificInstDirName : str
            Specific instrument directory name.
        instName : enum 'InstName'
            Instrument name.
        """

        configDir = self.ztaac.dataShare.getConfigDir()
        zkAndDofIdxArraySetFile = self.ztaac.dataShare._zkAndDofIdxArraySetFile
        zkAndDofIdxArraySetFilePath = zkAndDofIdxArraySetFile.getFilePath()
        zkAndDofIdxArraySetFileName = os.path.basename(zkAndDofIdxArraySetFilePath)

        specificZkAndDofIdxArraySetFileName = os.path.join(
            specificInstDirName, zkAndDofIdxArraySetFileName)
        self.ztaac.dataShare.config(
            configDir, instName,
            zkAndDofIdxArraySetFileName=specificZkAndDofIdxArraySetFileName)


if __name__ == "__main__":
    pass
