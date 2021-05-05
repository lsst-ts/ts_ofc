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

__all__ = ["BaseOFCData", "default_eff_wavelenght"]

import numpy as np

from dataclasses import dataclass, field


def default_eff_wavelenght():
    """Default effective wavelenght.

    Returns
    -------
    `dict`
        Filter name and associated effective wavelength in um.
    """
    return {
        "U": 0.365,
        "G": 0.480,
        "R": 0.622,
        "I": 0.754,
        "Z": 0.868,
        "Y": 0.973,
        "": 0.5,  # Reference effective wavelenght.
    }


@dataclass
class BaseOFCData:
    """Base Optical Feedback Control Data.

    Attributes
    ----------
    alpha : `np.array` of `float`
        Alpha coefficient for the normalized point-source sensitivity (PSSN).
    control_strategy : `string`
        Name of the control strategy.
    delta : `np.array` of `float`
        Delta coefficient for the normalized point-source sensitivity (PSSN).
    dof_state0_filename : `string`
        Name of the file with the initial degrees of freedom.
    eff_wavelength : `dict` of `string`
        Effective wavelength in um for each filter.
    intrinsic_zk_filename_root : `string`
        Filename root string for the intrinsic zernike coefficients.
    iqw_filename : `str`
        Image quality weight filename.
    m1m3_actuator_penalty : `float`
        M1M3 actuator penalty factor.
    m2_actuator_penalty : `float`
        M2 actuator penalty factor.
    motion_penalty : `float`
        Penalty on control motion as a whole.
    rb_stroke : `np.array` of `float`
        Allowed moving range of rigid body of M2 hexapod and Camera hexapod in
        the unit of um. e.g. rbStroke[0] means the M2 piston is allowed to move
        +5900 um to -5900 um.
    sen_m_filename_root : `string`
        Filename root string for the sensitivity matrix M.
    sensor_mapping_filename : `string`
        Name of the file with the mapping between the sensor name and field
        index.
    y2_filename : `string`
        Name of the file where `y2_correction` is read from.
    zn3_idx : `np.array` of `bool`
        Index of annular Zernike polynomials (z3-z22) (`True`: in use, `False`:
        not in use).
    zn3_idx_in_intrinsic_zn_file : `int`
        Specify where the zernike data starts when reading the intrinsic
        zernike coefficients.
    znmax : `int`
        Max number of zernikes used (to be filtered with `zn3_idx`).
    """

    iqw_filename: str = "imgQualWgt.yaml"
    y2_filename: str = "y2.yaml"
    sensor_mapping_filename: str = "sensorNameToFieldIdx.yaml"
    dof_state0_filename: str = "state0inDof.yaml"
    intrinsic_zk_filename_root: str = "intrinsicZn"
    sen_m_filename_root: str = "senM"

    zn3_idx_in_intrinsic_zn_file: int = 3

    eff_wavelength: dict = field(default_factory=default_eff_wavelenght)

    znmax: int = 22  # Max number of zernikes used (to be filtered with zn3Idx)

    zn3_idx: np.ndarray = np.arange(19)
    # Index of annular Zernike polynomials (z3-z22)

    # Control strategy
    control_strategy: str = "optiPSSN"

    # M1M3 actuator penalty factor
    # how many microns of M2 piston does 1N rms force correspond to
    # the bigger the number, the bigger the penalty
    # 13.2584 below = 5900/445
    # 445 means 445N, rms reaching 445N is as bad as M2 piston reaching
    # 5900um
    m1m3_actuator_penalty: float = 13.2584

    # M2 actuator penalty factor
    # how many microns of M2 piston does 1N rms force correspond to
    # the bigger the number, the bigger the penalty
    # M2 F budget for AOS = 44N. 5900/44 = 134
    m2_actuator_penalty: float = 134.0

    # penalty on control motion as a whole
    # default below is 0.001, meaning 1N force is as bad as 0.001 increase
    # in pssn use 0, if you accept whatever motion needed to produce best
    # image quality use 1e100, if you absolutely hate anything that moves
    motion_penalty: float = 0.001

    # Normalized point-source sensitivity (PSSN) information
    # PSSN ~ 1 - alpha * delta^2
    # Eq (7.1) in Normalized Point Source Sensitivity for LSST
    # (document-17242). It is noted that there are 19 terms of alpha value
    # here for z4-z22 to use.

    alpha: np.ndarray = np.array(
        [
            6.6906168e-03,
            9.4460611e-04,
            9.4460611e-04,
            6.1240430e-03,
            6.1240430e-03,
            1.7516747e-03,
            1.7516747e-03,
            4.9218300e-02,
            9.4518035e-03,
            9.4518035e-03,
            3.0979027e-03,
            3.0979027e-03,
            4.5078901e-02,
            4.5078901e-02,
            1.2438449e-02,
            1.2438449e-02,
            4.5678764e-03,
            4.5678764e-03,
            3.6438430e-01,
        ]
    )
    delta: np.ndarray = np.array(
        [
            2.6353589e00,
            5.2758650e00,
            5.2758650e00,
            1.6866297e00,
            1.6866297e00,
            5.1471854e00,
            5.1471854e00,
            8.6355441e-01,
            1.6866297e00,
            1.6866297e00,
            2.7012429e00,
            2.7012429e00,
            4.4213986e-01,
            4.4213986e-01,
            1.6866297e00,
            1.6866297e00,
            1.6866297e00,
            1.6866297e00,
            2.8296951e-01,
        ]
    )

    # Allowed moving range of rigid body of M2 hexapod and Camera hexapod
    # in the unit of um. e.g. rbStroke[0] means the M2 piston is allowed to
    # move +5900 um to -5900 um.
    rb_stroke: np.ndarray = np.array(
        [5900, 6700, 6700, 432, 432, 8700, 7600, 7600, 864, 864]
    )
