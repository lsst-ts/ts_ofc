import os
import re
import numpy as np

from lsst.ts.ofc.Utility import InstName, FilterType, DofGroup, \
                                getMatchFilePath, getSetting, \
                                getDirFiles


class OptStateEsti(object):

    def estiOptState(self, filterType, wfErr, fieldIdx):
        """Estimate the optical state in the basis of degree of
        freedom (DOF).

        Solve y = A*x by x = pinv(A)*y.

        Parameters
        ----------
        filterType : enum 'FilterType'
            Active filter type.
        wfErr : numpy.ndarray
            Wavefront error im um.
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        Returns
        -------
        numpy.ndarray
            Optical state in the basis of DOF.
        """

        wfErr = wfErr[:, self.zn3Idx].reshape(-1, 1)
        intrinsicZk = self._getIntrinsicZk(filterType, fieldIdx)
        y2c = self.getY2Corr(fieldIdx, isNby1Array=True)

        # senA = self._setSenA(fieldIdx)
        # pinvA = self._setPinvA(rcond)

        y = wfErr - intrinsicZk - y2c
        x = self.pinvA.dot(y)

        return x.ravel()

    def setAandPinvA(self, fieldIdx, rcond=1e-4):
        """Set the sensitivity matrix A and the related pseudo-inverse
        A^(-1).

        Parameters
        ----------
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.
        rcond : float, optional
            Cutoff for small singular values. (the default is 1e-4.)
        """

        self._setSenA(fieldIdx)
        self._setPinvA(rcond)

    def _setSenA(self, fieldIdx):
        """Set the sensitivity matrix A based on the array of field index.

        Parameters
        ----------
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        Raises
        ------
        RuntimeError
            Equation number < variable number.
        """

        # Constuct the sensitivity matrix A
        self.matA = self.senM[fieldIdx, :, :]
        self.matA = self.matA.reshape((-1, self.senM.shape[2]))

        # Check the dimension of pinv A
        numOfZkEq, numOfDof = self.matA.shape
        if (numOfZkEq < numOfDof):
            raise RuntimeError("Equation number < variable number.")

    def _setPinvA(self, rcond=1e-4):
        """Set the pueudo-inversed matrix A with the truncation.

        Parameters
        ----------
        rcond : float
            Cutoff for small singular values.
        """

        self.pinvA = np.linalg.pinv(self.matA, rcond=rcond)



if __name__ == "__main__":
    pass
