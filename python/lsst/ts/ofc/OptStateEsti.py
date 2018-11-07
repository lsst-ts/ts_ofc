import numpy as np


class OptStateEsti(object):

    def estiOptState(self, dataShare, filterType, wfErr, fieldIdx):
        """Estimate the optical state in the basis of degree of
        freedom (DOF).

        Solve y = A*x by x = pinv(A)*y.

        Parameters
        ----------
        dataShare: DataShare
            Instance of DataShare class.
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

        zn3Idx = dataShare.getZn3Idx()
        wfErr = wfErr[:, zn3Idx].reshape(-1, 1)
        intrinsicZk = dataShare.getIntrinsicZk(filterType, fieldIdx)
        y2c = dataShare.getY2Corr(fieldIdx, isNby1Array=True)
        y = wfErr - intrinsicZk - y2c

        senM = dataShare.getSenM()
        matA = self._getSenA(senM, fieldIdx)
        rcond = 1e-4
        pinvA = self._getPinvA(matA, rcond)

        x = pinvA.dot(y)

        return x.ravel()

    def _getSenA(self, senM, fieldIdx):
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
