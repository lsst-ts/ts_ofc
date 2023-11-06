# This file is part of ts_ofc
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

__all__ = ["get_intrinsic_zernikes"]

import galsim
import numpy as np

from ..ofc_data import OFCData


def get_intrinsic_zernikes(
    ofc_data: OFCData,
    filter_name: str,
    sensor_names: list[str],
    rotation_angle: float = 0.0,
) -> np.ndarray:
    """Return reformated instrisic zernike coefficients.

    Parameters
    ----------
    filter_name : `string`
        Name of the filter to get intrinsic zernike coefficients. Must be
        in the `intrinsic_zk` dictionary.
    field_angles : `list` [`string`]
        List of sensor names.
    rotation_angle : `float`, optional
        Rotation angle in degrees.

    Raises
    ------
    RuntimeError :
        If `filter_name` not valid.
    """
    if filter_name not in ofc_data.intrinsic_zk:
        raise RuntimeError(
            f"Invalid filter name {filter_name}. Must be one of {ofc_data.intrinsic_zk.keys()}."
        )

    # Get the field angles for the sensors
    field_angles = [ofc_data.sample_points[sensor] for sensor in sensor_names]
    field_x, field_y = zip(*field_angles)

    # Convert rotation angle to radians
    rotation_angle = np.deg2rad(rotation_angle)

    evaluated_zernikes = np.array(
        [
            zk.coef
            for zk in galsim.zernike.DoubleZernike(
                ofc_data.intrinsic_zk[filter_name],
                # Rubin annuli
                uv_inner=ofc_data.config["pupil"]["R_inner"],
                uv_outer=ofc_data.config["pupil"]["R_outer"],
                xy_inner=ofc_data.config["obscuration"]["R_inner"],
                xy_outer=ofc_data.config["obscuration"]["R_outer"],
            ).rotate(theta_uv=rotation_angle)(field_x, field_y)
        ]
    )

    evaluated_zernikes *= ofc_data.eff_wavelength[filter_name]

    return evaluated_zernikes[:, ofc_data.znmin : ofc_data.znmax + 1]
