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

__all__ = ["OFCData"]

import re
import yaml
import asyncio
import logging

import numpy as np

from glob import glob
from pathlib import Path

from .utils import get_config_dir

_INTRISICZN_FILTER_REGEX = re.compile(r"intrinsicZn(?P<name>[a-zA-Z_-]*).yaml")


class OFCData:
    """Optical Feedback Control Data.

    This container class provides a unified interface to all the data used by
    the OFC and its ancillary classes. It provides utiliy to load, inspect and
    update the different configuration files used by these classes.

    Parameters
    ----------
    name : `string`
        Name of the instrument/configuration. This must map to a directory
        inside `data_path`.
    config_dir : `string` or `None`
        Path to configuration directory. If `None` (default) use data provided
        with the module. If a `string` is provided it must map to a valid path.
    log : `logging.Logger` or `None`
        Optional logging class to be used for logging operations. If `None`,
        creates a new logger.

    Attributes
    ----------
    alpha : `np.array` of `float`
        Alpha coefficient for the normalized point-source sensitivity (PSSN).
    config_dir : `pathlib.Path`
        Path to the directory storing configuration files.
    control_strategy : `string`
        Name of the control strategy.
    delta : `np.array` of `float`
        Delta coefficient for the normalized point-source sensitivity (PSSN).
    dof_idx : `dict` of `string`
        Index of Degree of Freedom (DOF).
    eff_wavelength : `dict` of `string`
        Effective wavelength in um for each filter.
    field_idx : `dict` of `string`
        Mapping between sensor name and field index.
    idx_dof : `dict` of `string`
        Index of Degree of Freedom (DOF)
    intrinsic_zk : `dict` of `string`
        Intrinsic zernike coefficients per band per detector for a specific
        instrument configuration.
    intrinsic_zk_filename_root : `string`
        Filename root string for the intrinsic zernike coefficients.
    log : `logging.Logger`
        Logger class used for logging operations.
    m1m3_actuator_penalty : `float`
        M1M3 actuator penalty factor.
    m2_actuator_penalty : `float`
        M2 actuator penalty factor.
    motion_penalty : `float`
        Penalty on control motion as a whole.
    name : `string`
        Name of the instrument configuration. This is used to define where
        `intrinsic_zk` and `y2` will be read from.
    rb_stroke : `np.array` of `float`
        Allowed moving range of rigid body of M2 hexapod and Camera hexapod in
        the unit of um. e.g. rbStroke[0] means the M2 piston is allowed to move
        +5900 um to -5900 um.
    sensitivity_matrix : `np.ndarray` of `float`
        Sensitivity matrix M.
    sen_m_filename_root : `string`
        Filename root string for the sensitivity matrix M.
    sensor_mapping_filename : `string`
        Name of the file with the mapping between the sensor name and field
        index.
    start_task : `asyncio.Future`
        Asyncio future that tracks whether the class is setup and ready or not.
    xref : `string`
        Define how the control strategy will handle the reference point.
    xref_list : `list` of `string`
        Available reference point strategies.
    y2_correction : `np.ndarray` of `float`
        Y2 correction.
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

    Raises
    ------
    RuntimeError
        If input `config_dir` does not exists.
    """

    def __init__(self, name, config_dir=None, log=None):

        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        if config_dir is None:
            self.log.debug("Using default configuration directory.")
            self.config_dir = get_config_dir()
        else:
            self.log.debug(
                f"Using user-provided configuration directory: {config_dir}."
            )
            self.config_dir = Path(config_dir)
            if not self.config_dir.exists():
                raise RuntimeError(
                    f"Provided data path ({self.config_dir}) does not exists."
                )

        self.iqw_filename = "imgQualWgt.yaml"
        self.y2_filename = "y2.yaml"
        self.sensor_mapping_filename = "sensorNameToFieldIdx.yaml"
        self.dof_state0_filename = "state0inDof.yaml"
        self.intrinsic_zk_filename_root = "intrinsicZn"
        self.sen_m_filename_root = "senM"

        # Dictionary to hold bending mode data. The data is read alongside the
        # other files when the name is set.
        self.bend_mode = {
            "M1M3": {
                "force": {"filename": "M1M3_1um_156_force.yaml"},
                "rot": {"filename": "rotMatM1M3.yaml"},
            },
            "M2": {
                "force": {"filename": "M2_1um_72_force.yaml"},
                "rot": {"filename": "rotMatM2.yaml"},
            },
        }

        self.zn3_idx_in_intrinsic_zn_file = 3

        # Set the name of the instrument. This reads the instrument-related
        # configuration files. The read is done in the background by scheduling
        # a process in the event loop.

        self.start_task = asyncio.Future()
        self.start_task.set_result(None)
        self._configure_task = None
        self.name = name

        # Filter name and associated effective wavelength in um.

        self.eff_wavelength = {
            "U": 0.365,
            "G": 0.480,
            "R": 0.622,
            "I": 0.754,
            "Z": 0.868,
            "Y": 0.973,
            "": 0.5,
        }

        # Max number of zernikes used (to be filtered with zn3Idx)
        self.znmax = 22

        # Rotation matrix between ZEMAX coordinate and optical coordinate
        # systems defined in LTS-136.
        #
        # In ZEMAX coordinate, the hexapod position is (z', x', y', rx', ry').
        # +z' is defined from M2 to M1M3.
        # +y' is defined as pointing toward zenith when the telescope is
        # pointed toward the horizon (elevation angle is 0 degree).
        # +x' follows by the right hand rule.
        # x', y', and z' are in um. rx' and ry' are in the arcsec.
        #
        # In optical coordinate system, the hexapod position is (x, y, z, rx,
        # ry, rz).
        # +z is defined from M1M3 to M2. +y is defined as pointing toward
        # zenith when the telescope is pointed toward the horizon (elevation
        # angle is 0 degree).
        # +x follows by the right hand rule.
        # x, y, and z are in um. rx, ry, and rz are in the degree.
        #
        # For the rotation matrix below, row is (z', x', y', rx', ry') and
        # column is (x, y, z, rx, ry, rz).
        #
        # 1 degree = 3600 arcsec
        rot_mat_hexapod = np.array(
            [
                [0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
                [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, -3600.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, -3600.0, 0.0],
            ]
        )

        # Index of Degree of Freedom (DOF)
        self.comp_dof_idx = dict(
            m2HexPos=dict(
                startIdx=0, idxLength=5, state0name="M2Hexapod", rot_mat=rot_mat_hexapod
            ),
            camHexPos=dict(
                startIdx=5,
                idxLength=5,
                state0name="cameraHexapod",
                rot_mat=rot_mat_hexapod,
            ),
            M1M3Bend=dict(
                startIdx=10, idxLength=20, state0name="M1M3Bending", rot_mat=1.0
            ),
            M2Bend=dict(startIdx=30, idxLength=20, state0name="M2Bending", rot_mat=1.0),
        )

        # Index of degree of freedom
        self._dof_idx = np.arange(
            sum([self.comp_dof_idx[comp]["idxLength"] for comp in self.comp_dof_idx])
        )

        self._dof_idx_mask = np.ones_like(self._dof_idx, dtype=bool)

        # Index of annular Zernike polynomials (z3-z22)
        self.zn3_idx = np.arange(19)

        # Parameters for the AOS controller

        # Control strategy
        self.control_strategy = "optiPSSN"
        self.xref_list = ["x00", "x0", "0"]
        self.xref = "x00"

        # M1M3 actuator penalty factor
        # how many microns of M2 piston does 1N rms force correspond to
        # the bigger the number, the bigger the penalty
        # 13.2584 below = 5900/445
        # 445 means 445N, rms reaching 445N is as bad as M2 piston reaching
        # 5900um
        self.m1m3_actuator_penalty = 13.2584

        # M2 actuator penalty factor
        # how many microns of M2 piston does 1N rms force correspond to
        # the bigger the number, the bigger the penalty
        # M2 F budget for AOS = 44N. 5900/44 = 134
        self.m2_actuator_penalty = 134

        # penalty on control motion as a whole
        # default below is 0.001, meaning 1N force is as bad as 0.001 increase
        # in pssn use 0, if you accept whatever motion needed to produce best
        # image quality use 1e100, if you absolutely hate anything that moves
        self.motion_penalty = 0.001

        # Normalized point-source sensitivity (PSSN) information
        # PSSN ~ 1 - alpha * delta^2
        # Eq (7.1) in Normalized Point Source Sensitivity for LSST
        # (document-17242). It is noted that there are 19 terms of alpha value
        # here for z4-z22 to use.

        self.alpha = np.array(
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
        self.delta = np.array(
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
        self.rb_stroke = np.array(
            [5900, 6700, 6700, 432, 432, 8700, 7600, 7600, 864, 864]
        )

    @property
    def name(self):
        if not self.start_task.done():
            raise RuntimeError(
                "Class not setup or still loading instrument files."
                "You must await for `start_task` to complete."
            )
        return self.start_task.result()

    @name.setter
    def name(self, value):

        # Check if event loop is running. If not, setup as normal method.
        if not self.start_task.get_loop().is_running():
            self.start_task = asyncio.Future()
            self._configure_instrument(value)
        elif not self.start_task.done():
            raise RuntimeError(
                "Instrument being configured. Cannot interrupt process. "
                "Wait for `start_task` to complete before setting instrument again."
            )
        else:
            loop = asyncio.get_running_loop()
            self.start_task = asyncio.Future()
            self._configure_task = loop.run_in_executor(
                None, self._configure_instrument, value
            )

    @property
    def dof_idx(self):
        return self._dof_idx[self._dof_idx_mask]

    @dof_idx.setter
    def dof_idx(self, value):
        if not isinstance(value, dict):
            raise ValueError(
                f"dof_idx must be a dictionary with {self.comp_dof_idx.keys()} entries."
            )

        for comp in self.comp_dof_idx:
            start_idx = self.comp_dof_idx[comp]["startIdx"]
            length = self.comp_dof_idx[comp]["idxLength"]
            end_idx = start_idx + length

            if len(value[comp]) != length:
                raise RuntimeError(
                    f"Size of input vector ({len(value[comp])}) different than expected ({length})."
                )
            if (
                not isinstance(value[comp], np.ndarray)
                or not value[comp].dtype.type is np.bool_
            ):
                raise RuntimeError("Input should be np.ndarray of type bool.")
            self._dof_idx_mask[start_idx:end_idx] = value[comp]

    def get_intrinsic_zk(self, filter_name, field_idx=None):
        """Return reformated instrisic zernike coefficients.

        Parameters
        ----------
        filter_name : `string`
            Name of the filter to get intrinsic zernike coefficients. Must be
            in the `intrinsic_zk` dictionary.
        field_idx : `np.ndarray` or `None`, optional
            Array with the field indexes to get instrisic data from (default
            `None`). If not given, return all available data.

        Raises
        ------
        RuntimeError :
            If `filter_name` not valid.
        """
        if filter_name not in self.intrinsic_zk:
            raise RuntimeError(
                f"Invalid filter name {filter_name}. Must be one of {self.intrinsic_zk.keys()}."
            )

        _field_idx = (
            field_idx
            if field_idx is not None
            else np.arange(self.intrinsic_zk[filter_name].shape[0])
        )

        return (
            self.intrinsic_zk[filter_name][
                np.ix_(
                    _field_idx,
                    self.zn3_idx + self.zn3_idx_in_intrinsic_zn_file,
                )
            ]
            * self.eff_wavelength[filter_name]
        )

    async def close(self):
        """Close method.

        The method checks if `_configure_task` is completed. If not, cancel it
        and wait for it to complete.
        """

        if not self._configure_task.done():
            self._configure_task.cancel()

        try:
            await self._configure_task
        except asyncio.CancelledError:
            self.log.debug("Configure task cancelled.")
        except Exception:
            self.log.exception("Error in configure task.")

    def _configure_instrument(self, value):
        """Configure OFCData instrument.

        Parameters
        ----------
        value : `string`
            Name of the instrument.

        Raises
        ------
        RuntimeError
            If instrument configuration directory does not exists.
            If y2 configuration files does not exists in the configuration
            directory.
            If intrinsic zernike coefficients files does not exists in the
            configuration directory.
            If image quality weight file not exists in the configuration
            directory.
        """

        self.log.debug("Reading bend mode data.")

        for comp in self.bend_mode:
            for ftype in self.bend_mode[comp]:
                if "data" in self.bend_mode[comp][ftype]:
                    self.log.debug(f"Data for {comp}:{ftype} already read, skipping...")
                else:
                    self.log.debug(f"Reading {comp}:{ftype} data.")
                    path = (
                        self.config_dir / comp / self.bend_mode[comp][ftype]["filename"]
                    )
                    with open(path) as fp:
                        self.bend_mode[comp][ftype]["data"] = yaml.safe_load(fp)

        self.log.debug(f"Configuring {value}")

        inst_config_dir = self.config_dir / value
        if not inst_config_dir.exists():
            RuntimeError(
                f"Instrument {inst_config_dir!s} configuration directory does not exists. "
                f"Make sure the name you are passing ({value}) exists in the configuration directory: "
                f"{self.config_dir!s}."
            )

        # Load all data to local variables and only set them at the end if
        # everthing went fine. Otherwise you can leave the class in a broken
        # state.

        # Read dof_state0
        dof_state0_path = inst_config_dir / self.dof_state0_filename

        with open(dof_state0_path) as fp:
            dof_state0 = yaml.safe_load(fp)

        # Read image quality weight
        iqw_path = inst_config_dir / self.iqw_filename

        self.log.debug(f"Configuring image quality weight: {iqw_path}")

        try:
            with open(iqw_path) as fp:
                data = yaml.safe_load(fp)
                # This data has an "interesting" format. The first column is
                # the index of the sensor and the second is the weight. It kind
                # of makes sense to use it this way because it is a detector
                # index not just the line number. In any case, we must make
                # sure we respect the index on the first column. This is not
                # exactly efficient but better than risk users entering data
                # out-of-order expecting the code to handle it and doesn't
                image_quality_weight = np.zeros(len(data))
                index = np.array([k for k in data.keys()], dtype=int)
                _data = np.array([data[k] for k in data])
                image_quality_weight[index] = _data
        except FileNotFoundError:
            raise RuntimeError(
                f"Could not read image quality file from instrument config directory: {iqw_path!s}. "
                "Check your instrument configuration directory integrity."
            )

        # Read y2 file
        y2_path = inst_config_dir / self.y2_filename

        self.log.debug(f"Configuring y2: {y2_path}")

        try:
            with open(y2_path) as fp:
                y2_correction = np.array(yaml.safe_load(fp))
        except FileNotFoundError:
            raise RuntimeError(
                f"Could not read y2 file from instrument config directory: {y2_path!s}. "
                "Check your instrument configuration directory integrity."
            )

        # Read all intrinsic zernike coefficients data.
        # Get filenames.
        intrinsic_zk_pattern = f"{self.intrinsic_zk_filename_root}*.yaml"
        izk_filenames = [
            Path(_p) for _p in glob(str(inst_config_dir / intrinsic_zk_pattern))
        ]

        self.log.debug(f"Configuring instrisic zernikes: {len(izk_filenames)} files.")

        intrinsic_zk = dict()

        for filename in izk_filenames:
            filter_name_regex = _INTRISICZN_FILTER_REGEX.match(filename.name)
            if filter_name_regex is None:
                RuntimeError(
                    f"Could not parse filter for intrinsic zernike coefficient file {filename.name}. "
                    "Either remove or rename the file so it does not match the pattern "
                    f"{intrinsic_zk_pattern}."
                )

            filter_name = filter_name_regex["name"]

            if filter_name in intrinsic_zk:
                RuntimeError(
                    f"Filter name {filter_name} already accounted for. "
                    f"Make sure the files in {inst_config_dir} does not duplicate filter names."
                )

            with open(filename) as fp:
                intrinsic_zk[filter_name] = np.array(yaml.safe_load(fp))

        self.log.debug(f"Configuring sensor mapping: {self.sensor_mapping_filename}")

        with open(inst_config_dir / self.sensor_mapping_filename) as fp:
            field_idx = yaml.safe_load(fp)

        senm_file = Path(
            glob(str(inst_config_dir / f"{self.sen_m_filename_root}*.yaml"))[0]
        )

        self.log.debug(f"Configuring sensitivity matrix: {senm_file}")

        with open(senm_file) as fp:
            sen_m = np.array(yaml.safe_load(fp))

        self.log.debug(f"done {value}")
        # Now all data was read successfully, time to set it up.
        self.image_quality_weight = image_quality_weight
        self.normalized_image_quality_weight = image_quality_weight / np.sum(
            image_quality_weight
        )
        self.dof_state0 = dof_state0
        self.y2_correction = y2_correction
        self.intrinsic_zk = intrinsic_zk
        self.field_idx = field_idx
        self.sensitivity_matrix = sen_m
        self.start_task.set_result(value)

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, traceback):
        await self.close()
