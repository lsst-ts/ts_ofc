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

__all__ = ["Correction"]

import numpy as np

from .utils import CorrectionType


class Correction:
    r"""Container for corrections.

    Parameters
    ----------
    *args :
        Sequence of values for the corrections. Must be possible to cast floats
        from the inputs.

    Notes
    -----

    This class provides a easy way to convert a sequence of values into
    corrections. The inputs can be any array-like format, as long as their
    values can be casted into floats.

    The following are all valid ways of creating a correction object:

        >>> cam_hexapod = Correction(0., 0., 0., 0., 0., 0.)
        >>> m1m3 = Correction(np.zeros(156))

    To get the corrections back uses can simply call the object.

        >>> cam_hexapod()
            array([0., 0., 0., 0., 0., 0.])
    """

    valid_sizes = {6, 72, 156}

    size_to_correction_type = {
        6: CorrectionType.POSITION,
        72: CorrectionType.FORCE,
        156: CorrectionType.FORCE,
    }

    def __init__(self, *args):

        self.correction = np.copy(np.array(args, dtype=float).flatten())

        if len(self.correction) in self.valid_sizes:
            self.correction_type = self.size_to_correction_type[len(self.correction)]
        else:
            self.correction_type = CorrectionType.UNKNOWN

    def __repr__(self):
        return f"{self.correction_type!s}::{self.corrections.round(3)}"

    def __call__(self):
        """Calling a correction object will return the correction."""
        return self.correction


if __name__ == "__main__":
    pass
