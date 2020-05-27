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

from lsst.ts.ofc.OptCtrlDefault import OptCtrlDefault


class FWHMToPSSN(object):
    """Base class for converting FWHM data provided by DM to PSSN data
    utilized by OFC.

    Nominally the final implementation will be provided by SE.
    """

    def __init__(self):
        """Initialization of FWHM to PSSN class.

        FWHM: Full width at half maximum.
        PSSN: Normalized point source sensitivity.
        """
        super().__init__()

    def convertToPssn(self, fwhm):
        """Convert the FWHM data to PSSN.

        Take the array of FWHM values (nominally 1 per CCD) and convert
        it to PSSN (nominally 1 per CCD).

        Parameters
        ----------
        fwhm : numpy.ndarray[x]
            An array of FWHM values with sensor information.

        Returns
        -------
        numpy.ndarray[y]
            An array of PSSN values.
        """

        denominator = OptCtrlDefault.ETA * OptCtrlDefault.FWHM_ATM
        pssn = 1 / ((fwhm / denominator) ** 2 + 1)

        return pssn


if __name__ == "__main__":
    pass
