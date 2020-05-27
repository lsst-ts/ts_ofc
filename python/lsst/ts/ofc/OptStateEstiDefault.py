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


class OptStateEstiDefault(object):
    def estiOptState(self, optStateEstiData, filterType, wfErr, fieldIdx):
        """Estimate the optical state in the basis of degree of
        freedom (DOF).

        Parameters
        ----------
        optStateEstiData: OptStateEstiDataDecorator
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

        Raises
        ------
        NotImplementedError
            Child class should implemented this.
        """
        raise NotImplementedError("Child class should implemented this.")


if __name__ == "__main__":
    pass
