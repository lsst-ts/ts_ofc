# This file is part of ts_ofc.
#
# Developed for the LSST Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np


class OptCtrlDefault(object):

    # Eta in FWHM calculation.
    ETA = 1.086

    # FWHM in atmosphere.
    FWHM_ATM = 0.6

    def __init__(self):
        """Initialization of optimal control default class."""

        self.gain = 0
        self.state0InDof = np.array([])
        self.stateInDof = np.array([])

    def initStateToState0(self):
        """Initialize the state to the state 0 in the basis of degree of
        freedom (DOF)."""

        self.stateInDof = self.state0InDof.copy()

    def setState0(self, state0InDof):
        """Set the state 0 in degree of freedom (DOF).

        Parameters
        ----------
        state0InDof : numpy.ndarray or list
            State 0 in DOF.
        """

        self.state0InDof = np.array(state0InDof, dtype=float)

    def setState(self, stateInDof):
        """Set the state in degree of freedom (DOF).

        Parameters
        ----------
        stateInDof : numpy.ndarray or list
            State in DOF.
        """

        self.stateInDof = np.array(stateInDof, dtype=float)

    def getState0(self, dofIdx):
        """Get the state 0 in degree of freedom (DOF).

        Parameters
        ----------
        dofIdx : numpy.ndarray[int] or list[int]
            Index array of degree of freedom.

        Returns
        -------
        numpy.ndarray
            State 0 in DOF.
        """

        return self.state0InDof[dofIdx]

    def getState(self, dofIdx):
        """Get the state in degree of freedom (DOF).

        Parameters
        ----------
        dofIdx : numpy.ndarray[int] or list[int]
            Index array of degree of freedom.

        Returns
        -------
        numpy.ndarray
            State in DOF.
        """

        return self.stateInDof[dofIdx]

    def getNumOfState0(self):
        """Get the number of element of state 0.

        Returns
        -------
        int
            Number of element of state 0.
        """

        return len(self.state0InDof)

    def aggState(self, calcDof, dofIdx):
        """Aggregate the calculated degree of freedom (DOF) in the state.

        Parameters
        ----------
        calcDof : numpy.ndarray or list
            Calculated DOF.
        dofIdx : numpy.ndarray[int] or list[int]
            Index array of degree of freedom.
        """

        addDof = np.zeros(self.getNumOfState0(), dtype=float)
        addDof[dofIdx] = np.array(calcDof, dtype=float)

        self.stateInDof += addDof

    def getGroupDof(self, startIdx, groupLeng, inputDof=None):
        """Get the degree of freedom (DOF) of specific group based on the
        start index and length.

        If there is no input DOF, the output will be the aggregated DOF
        (state - state0). Otherwise, the output is based on the input DOF.

        The default output units are:
        1. M2 hexapod position (dz in um, dx in um, dy in um, rx in arcsec,
        ry in arcsec).
        2. Cam hexapod position (dz in um, dx in um, dy in um, rx in arcsec,
        ry in arcsec).
        3. M1M3 20 bending mode in um.
        4. M2 20 bending mode in um.

        Parameters
        ----------
        startIdx : int
            Start index of group.
        groupLeng : int
            Index length of group.
        inputDof : numpy.ndarray or list, optional
            Input DOF. (the default is None.)

        Returns
        -------
        numpy.ndarray
            DOF.
        """

        if inputDof is None:
            dof = self.stateInDof - self.state0InDof
        else:
            dof = np.array(inputDof)

        return dof[np.arange(startIdx, startIdx + groupLeng)]

    def setGain(self, gain):
        """Set the gain value.

        Parameters
        ----------
        gain : float
            Gain value in the feedback. It should be in the range of 0 and 1.

        Raises
        ------
        ValueError
            Gain is not in the range of [0, 1].
        """

        if 0 <= gain <= 1:
            self.gain = gain
        else:
            raise ValueError("Gain is not in the range of [0, 1].")

    def getGain(self):
        """Get the gain value.

        Returns
        -------
        float
            Gain value in the feedback.
        """

        return self.gain

    def calcEffGQFWHM(self, optCtrlDataDecorator, pssn, fieldIdx):
        """Calculate the effective FWHM by Gaussian quadrature.

        FWHM: Full width at half maximum.
        FWHM = eta * FWHM_{atm} * sqrt(1/PSSN -1).
        Effective GQFWHM = sum_{i} (w_{i}* FWHM_{i}).

        Parameters
        ----------
        optCtrlDataDecorator : OptCtrlDataDecorator
            Instance of OptCtrlDataDecorator class.
        pssn : numpy.ndarray or list
            Normalized point source sensitivity (PSSN).
        fieldIdx : numpy.ndarray[int] or list[int]
            Field index array.

        Returns
        -------
        float
            Effective FWHM in arcsec by Gaussain quadrature.

        Raises
        ------
        ValueError
            Input values are unphysical.
        """

        qWgt = optCtrlDataDecorator.getQwgt()
        fwhm = self.ETA * self.FWHM_ATM * np.sqrt(1 / np.array(pssn) - 1)
        fwhmGq = np.sum(qWgt[fieldIdx] * fwhm)

        if np.isnan(fwhmGq) or np.isinf(fwhmGq):
            raise ValueError("Input values are unphysical.")

        return fwhmGq

    def estiUkWithGain(self, optCtrlData, filterType, optSt):
        """Estimate uk in the basis of degree of freedom (DOF) with gain
        compensation.

        Parameters
        ----------
        optCtrlData: OptCtrlDataDecorator
            Instance of OptCtrlDataDecorator class that holds the DataShare
            instance.
        filterType : enum 'FilterType'
            Active filter type.
        optSt : numpy.ndarray
            Optical state in the basis of DOF.

        Returns
        -------
        numpy.ndarray
            Calculated uk in the basis of DOF.
        """

        return self.gain * self.estiUkWithoutGain(optCtrlData, filterType, optSt)

    def estiUkWithoutGain(self, optCtrlData, filterType, optSt):
        """Estimate uk in the basis of degree of freedom (DOF) without gain
        compensation.

        Parameters
        ----------
        optCtrlData: OptCtrlDataDecorator
            Instance of OptCtrlDataDecorator class that holds the DataShare
            instance.
        filterType : enum 'FilterType'
            Active filter type.
        optSt : numpy.ndarray
            Optical state in the basis of DOF.

        Returns
        -------
        numpy.ndarray
            Calculated uk in the basis of DOF.

        Raises
        ------
        NotImplementedError
            Child class should implemented this.
        """

        raise NotImplementedError("Child class should implemented this.")


if __name__ == "__main__":
    pass
