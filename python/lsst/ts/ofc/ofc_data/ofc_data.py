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

import asyncio
import logging
import re

from glob import glob
from pathlib import Path

from astropy.io import fits
import galsim
import numpy as np
import yaml

from ..utils import get_config_dir
from . import BaseOFCData


class OFCData(BaseOFCData):
    """Optical Feedback Control Data.

    This container class provides a unified interface to all the data used by
    the OFC and its ancillary classes. It provides utiliy to load, inspect and
    update the different configuration files used by these classes.

    Parameters
    ----------
    name : `string` or `None`, optional
        Name of the instrument/configuration. This must map to a directory
        inside `data_path`.
    config_dir : `string` or `None`, optional
        Path to configuration directory. If `None` (default) use data provided
        with the module. If a `string` is provided it must map to a valid path.
    log : `logging.Logger` or `None`, optional
        Optional logging class to be used for logging operations. If `None`,
        creates a new logger.
    kwargs : `dict`
        Additional keyword arguments. Value are passed over to the
        `BaseOFCData` parent class.

    Attributes
    ----------
    bend_mode : `dict`
        Dictionary to hold bending mode data. The data is read alongside the
        other files when the name is set.
    config_dir : `pathlib.Path`
        Path to the directory storing configuration files.
    control_strategy : `string`
        Name of the control strategy.
    dof_idx : `dict` of `string`
        Index of Degree of Freedom (DOF).
    field_idx : `dict` of `string`
        Mapping between sensor name and field index.
    idx_dof : `dict` of `string`
        Index of Degree of Freedom (DOF)
    intrinsic_zk : `dict` of `string`
        Intrinsic zernike coefficients per band per detector for a specific
        instrument configuration.
    log : `logging.Logger`
        Logger class used for logging operations.
    name : `string`
        Name of the instrument configuration. This is used to define where
        `intrinsic_zk` and `y2` will be read from.
    sensitivity_matrix : `np.ndarray` of `float`
        Sensitivity matrix M.
    start_task : `asyncio.Future`
        Asyncio future that tracks whether the class is setup and ready or not.
    xref : `string`
        Define how the control strategy will handle the reference point.
    xref_list : `list` of `string`
        Available reference point strategies.
    y2_correction : `np.ndarray` of `float`
        Y2 correction.

    Raises
    ------
    RuntimeError
        If input `config_dir` does not exists.
    """

    def __init__(self, name=None, config_dir=None, log=None, **kwargs):
        super().__init__(**kwargs)

        # Set logger
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        # Set configuration folder
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

        # Try to create a lock and a future. Sometimes it happens that the
        # event loop is closed, which raises a RuntimeError. If this happens,
        # create a new event loops and try again.
        try:
            self._configure_lock = asyncio.Lock()
            self.start_task = asyncio.Future()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
            self._configure_lock = asyncio.Lock()
            self.start_task = asyncio.Future()

        self.start_task.set_result(None)

        # Set the name of the instrument. This reads the instrument-related
        # configuration files.
        if name is not None:
            self.name = name

        rot_mat_hexapod: np.ndarray = np.array(
            [
                [0.0, 0.0, -1.0, 0.0, 0.0, 0.0],
                [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, -3600.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, -3600.0, 0.0],
            ]
        )

        # Index of Degree of Freedom (DOF)
        self._comp_dof_idx = dict(
            m2HexPos=dict(
                startIdx=0,
                idxLength=5,
                state0name="M2Hexapod",
                rot_mat=rot_mat_hexapod,
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

        # Control strategy
        self._xref = None

    @property
    def name(self):
        if not self.start_task.done() or self.start_task.result() is None:
            raise RuntimeError(
                "Class not setup or still loading instrument files."
                "You must await for `start_task` to complete."
            )
        return self.start_task.result()

    @name.setter
    def name(self, value):
        if not self.start_task.done():
            raise RuntimeError(
                "Instrument being configured. Cannot interrupt process. "
                "Wait for `start_task` to complete before setting instrument again."
            )
        else:
            self.start_task = asyncio.Future()
            self._configure_instrument(value)

    @property
    def xref(self):
        if self._xref is None:
            return "x00"
        else:
            return self._xref

    @xref.setter
    def xref(self, value):
        if value in self.xref_list:
            self._xref = value
        else:
            raise ValueError(
                f"Invalid xref value {value}. Must be one of {self.xref_list}."
            )

    @property
    def xref_list(self):
        return {"x00", "x0", "0"}

    @property
    def dof_idx(self):
        return self._dof_idx[self.dof_idx_mask]

    @property
    def dof_idx_mask(self):
        return self._dof_idx_mask

    @property
    def comp_dof_idx(self):
        return self._comp_dof_idx

    @comp_dof_idx.setter
    def comp_dof_idx(self, value):
        if not isinstance(value, dict):
            raise ValueError(
                f"comp_dof_idx must be a dictionary with {self.comp_dof_idx.keys()} entries."
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

    def get_intrinsic_zk(
        self,
        filter_name: str,
        field_idx: np.ndarray | None = None,
        rotation_angle: float = 0.0,
    ) -> np.ndarray:
        """Return reformated instrisic zernike coefficients.

        Parameters
        ----------
        filter_name : `string`
            Name of the filter to get intrinsic zernike coefficients. Must be
            in the `intrinsic_zk` dictionary.
        field_idx : `np.ndarray` or `None`, optional
            Array with the field indexes to get instrisic data from (default
            `None`). If not given, return all available data.
        rotation_angle : `float`, optional
            Rotation angle in degrees.

        Raises
        ------
        RuntimeError :
            If `filter_name` not valid.
        """
        if filter_name not in self.intrinsic_zk:
            raise RuntimeError(
                f"Invalid filter name {filter_name}. Must be one of {self.intrinsic_zk.keys()}."
            )

        if field_idx is None:
            field_x, field_y = zip(*self.gq_field_angles)
        else:
            gq_points = self.gq_field_angles[field_idx, :]
            field_x, field_y = zip(*gq_points)

        print(field_x, field_y)

        evaluated_zernikes = np.array(
            [
                zk.coef
                for zk in galsim.zernike.DoubleZernike(
                    self.intrinsic_zk[filter_name],
                    # Rubin annuli
                    uv_inner=self.config["pupil"]["R_inner"],
                    uv_outer=self.config["pupil"]["R_outer"],
                    xy_inner=self.config["obscuration"]["R_inner"],
                    xy_outer=self.config["obscuration"]["R_outer"],
                ).rotate(theta_uv=rotation_angle)(field_x, field_y)
            ]
        )

        evaluated_zernikes *= self.eff_wavelength[filter_name]

        return evaluated_zernikes[:, 4:23]

    async def configure_instrument(self, instrument: str) -> None:
        """Configure instrument concurrently.

        Parameters
        ----------
        instrument : `string`
            Name of the instrument.
        """
        async with self._configure_lock:
            self.start_task = asyncio.Future()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._configure_instrument, instrument)

    def _configure_instrument(self, instrument):
        """Configure OFCData instrument.

        Parameters
        ----------
        instrument : `string`
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

        self.log.debug(f"Configuring {instrument}")

        inst_config_dir = self.config_dir / instrument
        if not inst_config_dir.exists():
            RuntimeError(
                f"Instrument {inst_config_dir!s} configuration directory does not exists. "
                f"Make sure the name you are passing ({instrument}) exists in the configuration directory: "
                f"{self.config_dir!s}."
            )

        # Load all data to local variables and only set them at the end if
        # everthing went fine. Otherwise you can leave the class in a broken
        # state.

        # Read dof_state0
        dof_state0_path = self.config_dir / self.dof_state0_filename

        with open(dof_state0_path) as fp:
            dof_state0 = yaml.safe_load(fp)

        # Read image quality weight
        iqw_path = (
            self.config_dir
            / "sample_points"
            / instrument
            / self.iqw_filename
        )

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
        y2_path = self.config_dir / self.y2_filename

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
        self.log.debug(
            f"Configuring instrisic zernikes: {len(self.eff_wavelength.keys())} files."
        )

        intrinsic_zk = dict()
        camera_type = instrument if instrument != "lsstfam" else "lsst"
        intrinsic_zk_path = self.config_dir / "intrinsic_zernikes" / camera_type

        for filter_name in self.eff_wavelength.keys():
            file_name = f"{self.intrinsic_zk_filename_root}_{filter_name}_31*.yaml"
            intrinsic_file = Path(glob(str(intrinsic_zk_path / file_name))[0])

            with open(intrinsic_file) as fp:
                intrinsic_zk[filter_name] = np.array(yaml.safe_load(fp))

        self.log.debug(f"Configuring sensor mapping: {self.sensor_mapping_filename}")

        with open(
            self.config_dir
            / "sample_points"
            / instrument
            / self.sensor_mapping_filename
        ) as fp:
            field_idx = yaml.safe_load(fp)

        # Load the double zernikes sensitivity matrix
        senm_file = Path(
            glob(
                str(
                    self.config_dir
                    / "sensitivity_matrix"
                    / f"{camera_type}_{self.sen_m_filename_root}*.yaml"
                )
            )[0]
        )
        self.log.debug(f"Configuring sensitivity matrix: {senm_file}")

        with open(senm_file, "r") as fp:
            sen_m = np.array(yaml.safe_load(fp))

        with open(
            self.config_dir
            / "sample_points"
            / instrument
            / self.field_angles_filename
        ) as fp:
            gq_field_angles = np.array(yaml.safe_load(fp))
            gq_field_angles[:, 0] *= -1

        with open(
            self.config_dir / "configurations" / f"{camera_type}.yaml"
        ) as yaml_file:
            config = yaml.safe_load(yaml_file)

        self.log.debug(f"done {instrument}")
        # Now all data was read successfully, time to set it up.
        self.config = config
        self.image_quality_weight = image_quality_weight
        self.normalized_image_quality_weight = image_quality_weight / np.sum(
            image_quality_weight
        )
        self.dof_state0 = dof_state0
        self.y2_correction = y2_correction
        self.intrinsic_zk = intrinsic_zk
        self.field_idx = field_idx
        self.sensitivity_matrix = sen_m
        self.gq_field_angles = gq_field_angles
        self.start_task.set_result(instrument)

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, traceback):
        await self.close()
