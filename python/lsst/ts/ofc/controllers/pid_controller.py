# This file is part of ts_ofc.
#
# Developed for Vera Rubin Observatory.
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

from . import BaseController

__all__ = ["PIDController"]


class PIDController(BaseController):
    """PID controller."""

    def control_step(
        self,
        filter_name: str,
        dof_state: np.ndarray[float],
        sensor_names: list[str] | None = None,
    ) -> np.ndarray[float]:
        """Estimate the control offset for the given DOF state.

        Parameters
        ----------
        filter_name : `string`
            Name of the filter.
        dof_state : `numpy.ndarray`
            Optical state in the basis of DOF.
        sensor_names : `list` [`string`]
            List of sensor names.

        Returns
        -------
        control_effort : `numpy.ndarray`
            Calculated control_effort in the basis of DOF.
        """
        control_effort = self.calculate_pid_step(dof_state)

        return control_effort
