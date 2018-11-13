import numpy as np

from lsst.ts.ofc.OptStateEstiDefault import OptStateEstiDefault


class OptStateEsti(OptStateEstiDefault):

    RCOND = 1e-4

    def estiOptState(self, optStateEstiData, filterType, wfErr, fieldIdx):
        """Estimate the optical state in the basis of degree of
        freedom (DOF).

        Solve y = A*x by x = pinv(A)*y.

        Parameters
        ----------
        optStateEstiData: OptStateEstiData
            Instance of OptStateEstiDataDecorator class that holds the
            DataShare instance.
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

        intrinsicZk = optStateEstiData.getIntrinsicZk(filterType, fieldIdx)
        y2c = optStateEstiData.getY2Corr(fieldIdx)

        zn3Idx = optStateEstiData.getZn3Idx()
        y = wfErr[:, zn3Idx] - intrinsicZk - y2c
        y = y.reshape(-1, 1)

        senM = optStateEstiData.getSenM()
        matA = self._getMatA(senM, fieldIdx)
        pinvA = self._getPinvA(matA, self.RCOND)

        x = pinvA.dot(y)

        return x.ravel()

    def _getMatA(self, senM, fieldIdx):
        """Get the sensitivity matrix A based on the array of field index.

        Parameters
        ----------
        senM: numpy.ndarray
            Sensitivity matrix M.
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        Returns
        -------
        numpy.ndarray
            Sensitivity matrix A.

        Raises
        ------
        RuntimeError
            Equation number < variable number.
        """

        # Constuct the sensitivity matrix A
        matA = senM[fieldIdx, :, :]
        matA = matA.reshape((-1, senM.shape[2]))

        # Check the dimension of pinv A
        numOfZkEq, numOfDof = matA.shape
        if (numOfZkEq < numOfDof):
            raise RuntimeError("Equation number < variable number.")

        return matA

    def _getPinvA(self, matA, rcond):
        """Set the pueudo-inversed matrix A with the truncation.

        Parameters
        ----------
        mat: numpy.ndarray
            Sensitivity matrix A
        rcond : float
            Cutoff for small singular values.

        Returns
        -------
        numpy.ndarray
            Pueudo-inversed matrix A.
        """

        pinvA = np.linalg.pinv(matA, rcond=rcond)

        return pinvA


if __name__ == "__main__":
    pass
