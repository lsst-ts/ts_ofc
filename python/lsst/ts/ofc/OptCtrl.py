import os
import numpy as np

from lsst.ts.ofc.OptCtrlDefault import OptCtrlDefault
from lsst.ts.ofc.Utility import InstName, getSetting


class OptCtrl(OptCtrlDefault):

    def estiUkWithoutGain(self, optCtrlData, filterType, optSt):
        """Estimate uk by referencing to "0", "x0", or "x00" based on the
        configuration file without gain compensation..

        Parameters
        ----------
        optCtrlData : OptCtrlDataDecorator
            Instance of OptCtrlDataDecorator class that holds the DataShare instance.
        filterType : enum 'FilterType'
            Active filter type.
        optSt : numpy.ndarray
            Optical state in the basis of DOF.

        Returns
        -------
        numpy.ndarray
            Calculated uk in the basis of DOF.
        """

        ccMat = self._calcCCmat(optCtrlData, filterType)
        qx = self._calcQx(optCtrlData, ccMat, optSt)
        matF = self._calcMatF(optCtrlData, filterType)
        uk = self._calcUk(optCtrlData, matF, qx)

        return uk.ravel()

    def _calcCCmat(self, optCtrlData, filterType):
        """Calculate the CC matrix used in matrix Q.

        Cost function: J = x.T * Q * x + rho * u.T * H * u.
        Choose x.T * Q * x = p.T * p
        p = C * y = C * (A * x)
        p.T * p = (C * A * x).T * C * A * x
                = x.T * (A.T * C.T * C * A) * x = x.T * Q * x
        CCmat is C.T *C above.

        Parameters
        ----------
        optCtrlData : OptCtrlDataDecorator
            Instance of OptCtrlDataDecorator class that holds the DataShare instance.
        filterType : enum 'FilterType'
            Active filter type.

        Returns
        -------
        numpy.ndarray
            C.T * C matrix.
        """

        pssnAlpha = optCtrlData.getPssnAlphaFromFile()
        effWave = optCtrlData.getEffWave(filterType)
        zn3Idx = optCtrlData.getZn3Idx()

        ccMat = (2*np.pi/effWave)**2 * pssnAlpha[zn3Idx]
        ccMat = np.diag(ccMat)

        return ccMat

    def _calcQx(self, optCtrlData, ccMat, optSt):
        """Calculate the Qx.

        Qx = sum_{wi * A.T * C.T * C * (A * yk + y2k)}.

        Parameters
        ----------
        optCtrlData : OptCtrlDataDecorator
            Instance of OptCtrlDataDecorator class that holds the DataShare instance.
        ccMat : numpy.ndarray
            C.T * C matrix.
        optSt : numpy.ndarray
            Optical state in the basis of degree of freedom (DOF).

        Returns
        -------
        numpy.ndarray
            qx array.
        """

        optSt = optSt.reshape(-1, 1)

        qWgt = optCtrlData.getQwgtFromFile()
        senM = optCtrlData.getSenM()

        fieldNumInQwgt = optCtrlData.getNumOfFieldInQwgt()
        y2c = optCtrlData.getY2Corr(np.arange(fieldNumInQwgt))

        qx = 0
        for aMat, wgt, y2k in zip(senM, qWgt, y2c):
            y2k = y2k.reshape(-1, 1)
            qx += wgt * aMat.T.dot(ccMat).dot(aMat.dot(optSt) + y2k)

        return qx

    def _calcMatF(self, optCtrlData, filterType):
        """Calculate the F matrix.

        F = inv(A.T * C.T * C * A + rho * H).

        Parameters
        ----------
        optCtrlData : OptCtrlDataDecorator
            Instance of OptCtrlDataDecorator class that holds the DataShare instance.
        filterType : enum 'FilterType'
            Active filter type.
        """

        zn3Idx = optCtrlData.getZn3Idx()
        dofIdx = optCtrlData.getDofIdx()
        effWave = optCtrlData.getEffWave(filterType)

        authority = optCtrlData.getAuthority()
        matH = self._getMatH(authority, dofIdx)

        pssnAlpha = optCtrlData.getPssnAlphaFromFile()
        ccMat = self._calcCCmat(optCtrlData, filterType)

        qWgt = optCtrlData.getQwgtFromFile()
        senM = optCtrlData.getSenM()
        qMat = self._calcQmat(ccMat, senM, qWgt)

        penality = optCtrlData.getPenality()
        matF = self._calcF(qMat, matH, penality["Motion"])

        return matF

    def _getMatH(self, authority, dofIdx):
        """Get the matrix H used in the control algorithm.

        This matrix has considered the affection of penality on the
        authority of groups.

        Parameters
        ----------
        authority : numpy.ndarray
            Authority of subsystem. 
        dofIdx : numpy.ndarray[int] or list[int]
            Index array of degree of freedom.

        Returns
        -------
        numpy.ndarray
            Matrix H used in the cost function.
        """

        matH = np.diag(authority[dofIdx]**2)

        return matH

    def _calcQmat(self, ccMat, senM, qWgt):
        """Calculate the Q matrix used in the cost function.

        Qi = A.T * C.T * C * A for each field point.
        Final Q := sum_i (wi * Qi).

        Parameters
        ----------
        ccMat : numpy.ndarray
            C.T * C matrix.
        senM : numpy.ndarray
            Sensitivity matrix M.
        qWgt : numpy.ndarray
            Weighting ratio for the image quality Q matrix calculation.

        Returns
        -------
        numpy.ndarray
            Q matrix used in cost functin.
        """

        qMat = 0
        for aMat, wgt in zip(senM, qWgt):
            qMat += wgt * aMat.T.dot(ccMat).dot(aMat)

        return qMat

    def _calcF(self, qMat, matH, rho):
        """Calculate the F matrix.

        u = - A.T * C.T * C * A / (A.T * C.T * C * A + rho * H) * x0
          = - F * (A.T * C.T * C * A) * x0
        Q = A.T * C.T * C * A
        F = inv( A.T * C.T * C * A + rho * H )

        Parameters
        ----------
        qMat : numpy.ndarray
            Q matrix used in cost functin.
        matH : numpy.ndarray
            Matrix H used in the cost function.
        rho: floate
            Penality of motion.
        Returns
        -------
        numpy.ndarray
            F matrix.
        """

        # Because the unit is rms^2, the square of rho read from
        # the *.ctrl file is needed.
        matF = np.linalg.inv(rho**2 * matH + qMat)

        return matF

    def _calcUk(self, optCtrlData, matF, qx):
        """Calculate uk by referencing to "0", "x0", or "x00" based on
        the configuration file.

        Parameters
        ----------
        optCtrlData : OptCtrlDataDecorator
            Instance of OptCtrlDataDecorator class that holds the DataShare instance.
        matF : numpy.ndarray 
            Matrix F.
        qx : numpy.ndarray
            qx array.

        Returns
        -------
        numpy.ndarray
            Calculated uk in the basis of degree of freedom (DOF).

        Raises
        ------
        ValueError
            No Xref is assigned.
        """

        xRef = optCtrlData.getXref()
        if (xRef == "x0"):
            return self._calcUkRefX0(matF, qx)
        elif (xRef == "0"):
            return self._calcUkRef0(optCtrlData, matF, qx)
        elif (xRef == "x00"):
            return self._calcUkRefX00(optCtrlData, matF, qx)
        else:
            raise ValueError("No Xref is assigned.")

    def _calcUkRefX0(self, matF, qx):
        """Calculate uk by referencing to "x0".

        The offset will only trace the previous one.
        uk = -F' * QX.

        Parameters
        ----------
        matF : numpy.ndarray 
            Matrix F.
        qx : numpy.ndarray
            qx array.

        Returns
        -------
        numpy.ndarray
            Calculated uk in the basis of degree of freedom (DOF).
        """

        uk = -matF.dot(qx)

        return uk

    def _calcUkRef0(self, optCtrlData, matF, qx):
        """Calculate uk by referencing to "0".

        The offset will trace the real value and target for 0.
        uk = -F' * (QX + rho**2 * H * S).

        Parameters
        ----------
        optCtrlData : OptCtrlDataDecorator
            Instance of OptCtrlDataDecorator class that holds the DataShare instance.
        matF : numpy.ndarray 
            Matrix F.
        qx : numpy.ndarray
            qx array.

        Returns
        -------
        numpy.ndarray
            Calculated uk in the basis of degree of freedom (DOF).
        """

        authority = optCtrlData.getAuthority()
        dofIdx = optCtrlData.getDofIdx()
        matH = self._getMatH(authority, dofIdx)

        stateInDof = self.getState(dofIdx)
        stateInDof = stateInDof.reshape(-1, 1)

        penality = optCtrlData.getPenality()
        rho = penality["Motion"]
        qx += rho**2 * matH.dot(stateInDof)

        return self._calcUkRefX0(matF, qx)

    def _calcUkRefX00(self, optCtrlData, matF, qx):
        """Calculate uk by referencing to "x00".

        The offset will only trace the relative changes of offset without
        regarding the real value.
        uk = -F' * [QX + rho**2 * H * (S - S0)].

        Parameters
        ----------
        optCtrlData : OptCtrlDataDecorator
            Instance of OptCtrlDataDecorator class that holds the DataShare instance.
        matF : numpy.ndarray 
            Matrix F.
        qx : numpy.ndarray
            qx array.

        Returns
        -------
        numpy.ndarray
            Calculated uk in the basis of degree of freedom (DOF).
        """

        authority = optCtrlData.getAuthority()
        dofIdx = optCtrlData.getDofIdx()
        matH = self._getMatH(authority, dofIdx)

        stateInDof = self.getState(dofIdx)
        state0InDof = self.getState0(dofIdx)
        stateDiff = stateInDof - state0InDof
        stateDiff = stateDiff.reshape(-1, 1)

        penality = optCtrlData.getPenality()
        rho = penality["Motion"]

        qx += rho**2 * matH.dot(stateDiff)

        return self._calcUkRefX0(matF, qx)


if __name__ == "__main__":
    pass
