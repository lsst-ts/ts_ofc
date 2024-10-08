.. _user_guide:

#########################################
Optical Feedback Control (OFC) User Guide
#########################################

.. image:: https://img.shields.io/badge/GitHub-ts_ofc-green.svg
    :target: https://github.com/lsst-ts/ts_ofc
.. image:: https://img.shields.io/badge/Jenkins-ts_ofc-green.svg
    :target: https://tssw-ci.lsst.org/job/LSST_Telescope-and-Site/job/ts_ofc/
.. image:: https://img.shields.io/badge/Jira-ts_ofc-green.svg
    :target: https://jira.lsstcorp.org/issues/?jql=labels+%3D+ts_ofc

The :py:class:`Optical Feedback Control (OFC) <lsst.ts.ofc.OFC>` class is designed to compute corrections for the optical components given a set of wavefront errors for a group of sensors.
This is a fundamental part of the `MTAOS CSC`_.

.. _MTAOS CSC: https://ts-mtaos.lsst.io

In addition to its application in the `MTAOS CSC`_, users may be interested in using the :py:class:`OFC <lsst.ts.ofc.OFC>` in line to analyze results produced by the CSC or to study different configuration parameters and their effect in the results.

Before instantiating the :py:class:`OFC <lsst.ts.ofc.OFC>`, users must first create an instance of the :py:class:`OFCData <lsst.ts.ofc.OFCData>` class.
This class is responsible for storing and managing all data required for operations.
Via this data class, users are also free to modify the input parameters that affect the internal computations.

Users have the freedom to customize basically all parameters of the class either when creating the data class or afterwards.
Although the class provides some protection agains specifying unreasonable values, users must be aware that there might be some conditions where altering some data may render the class unusable.
Therefore, if you are experiencing issues running the OFC after altering some standard parameters, you may want to verify the changes you are doing.

The following provides an example of how one would use :py:class:`OFC <lsst.ts.ofc.OFC>` and :py:class:`OFCData <lsst.ts.ofc.OFCData>` to generate simple corrections from a list of wavefront errors.

.. code-block:: python

  import numpy as np

  from lsst.ts.ofc import OFC, OFCData

  ofc_data = OFCData("lsst")

  ofc = OFC(ofc_data)

  # create some data to process:
  wfe = np.zeros((4,19))
  sensor_names = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]

  # get corrections from ofc
  m2_hex, cam_hex, m1m3, m2 = ofc.calculate_corrections(
      wfe=wfe, sensor_names=sensor_names, filter_name="", rotation_angle=0.0
  )

  # Check the output
  m2_hex()
  cam_hex()
  m1m3()
  m2()

If you run the code above and check the output at the end, you will notice that, although we passed in only zeros as wavefront errors, we get non-zero corrections.
This is because the ``OFC`` takes into account the "intrinsic" wavefront error of each sensor.

You can check the intrinsic aberrations on the ``OFCData`` class:

.. code-block:: python

  ofc_data.intrinsic_zk

This is a dictionary that contains the intrinsic double zernike wavefront errors for each filter and for each sensor.
In the case above, we used the empty filter.
If you want to check the intrinsic aberrations for no filter at field points given by `field_angles` simply do:

.. code-block:: python

  from lsst.ts.ofc.utils import get_field_angles
  from lsst.ts.ofc.utils.intrinsic_zernikes import intrinsic_zernikes

  sensor_names = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]
  intrinsic_zks = intrinsic_zernikes(
      ofc_data, filter_name="R", sensor_names=sensor_names, rotation_angle=0.0
  )

You can also check what are the available filters with:

.. code-block:: python

  ofc_data.intrinsic_zk.keys()


A simple and useful test to perform is to pass the intrinsic aberrations to ofc, and check that it returns zeros for all the corrections.
This can be done with the following:

.. code-block:: python

  sensor_names = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]
  wfe = intrinsic_zernikes(
      ofc_data, filter_name="R", sensor_names=sensor_names, rotation_angle=0.0
  )

  # get corrections from ofc
  m2_hex, cam_hex, m1m3, m2 = ofc.calculate_corrections(
      wfe=wfe, sensor_names=sensor_names, filter_name="R", rotation_angle=0.0
  )

  # The corrections now should be all zeros
  m2_hex()
  cam_hex()
  m1m3()
  m2()

From the intrinsic corrections you can also easily obtain offsets to add aberrations.
This is, for instance, how the `MTAOS addAberration command`_ works:

.. _MTAOS addAberration command: https://ts-mtaos.lsst.io/user-guide/user-guide.html#adding-aberration


For instance, one can disable operations will all components except the Camera Hexapod by doing the following:

.. code-block:: python

  sensor_names = ["R00_SW0", "R04_SW0", "R40_SW0", "R44_SW0"]
  wfe = intrinsic_zernikes(
      ofc_data, filter_name="R", sensor_names=sensor_names, rotation_angle=0.0
  )
  wfe[:,0:1] += 0.1  # add 0.1 um of defocus

  # Disable all corrections except camera hexapod
  new_comp_dof_idx = dict(
      m2HexPos=np.zeros(5, dtype=bool),
      camHexPos=np.ones(5, dtype=bool),
      M1M3Bend=np.zeros(20, dtype=bool),
      M2Bend=np.zeros(20, dtype=bool),
  )

  self.ofc.ofc_data.comp_dof_idx = new_comp_dof_idx

  # get corrections from ofc
  m2_hex, cam_hex, m1m3, m2 = ofc.calculate_corrections(
      wfe=wfe, sensor_names=sensor_names, filter_name="R", rotation_angle=0.0
  )

  print(cam_hex)
  # Should print:
  # CorrectionType.POSITION::[ 0.    -0.    -6.271  0.     0.     0.   ]

This should result in only an offset in z-axis for the camera hexapod.

.. _OFC-User-Guide-Configuration-Files:

Configuration Files
-------------------

The OFC relies on a series of configuration files (managed by the :py:class:`OFCData <lsst.ts.ofc.OFCData>` class) that affect the underlying computations; ranging from the instrument configuration to converting wavefront errors to forces.

Standard configuration files are provided in the ``policy/`` directory on the root of the package.

Users can also customize where the :py:class:`OFCData <lsst.ts.ofc.OFCData>` class searches for configuration files when instantiating the class, e.g.:

.. code-block:: python

  # Use absolute path
  ofc_data = OFCData("lsst", "/home/username/ofc_config_dir/")

  # Use relative path
  ofc_data = OFCData("lsst", "./ofc_config_dir/")

The basic structure of a configuration directory is as follows:

.. code-block:: rst

  ofc_config_dir
  ├── M1M3
  │   ├── M1M3_1um_156_force.yaml
  │   └── rotMatM1M3.yaml
  ├── M2
  │   ├── M2_1um_72_force.yaml
  │   └── rotMatM2.yaml
  ├── configurations
  │   ├── comcam.yaml
  │   ├── pid_controller.yaml
  │   ├── oic_controller.yaml
  │   └── lsst.yaml
  ├── image_quality_weights
  │   ├── comcam_weights.yaml
  │   ├── lsst_gaussian_quadrature_weights.yaml
  │   ├── lsst_weights.yaml
  │   └── lsstfam_weights.yaml
  ├── sample_points
  │   ├── comcam_points.yaml
  │   ├── lsst_gaussian_quadrature_points.yaml
  │   ├── lsst_points.yaml
  │   └── lsstfam_points.yaml
  ├── intrinsic zernikes
  │   ├── comcam
  │   │   ├── intrinsic_zk__K_J.yaml
  │   │   ├── intrinsic_zk_g_K_J.yaml
  │   │   ├── intrinsic_zk_i_K_J.yaml
  │   │   ├── intrinsic_zk_r_K_J.yaml
  │   │   ├── intrinsic_zk_u_K_J.yaml
  │   │   ├── intrinsic_zk_y_K_J.yaml
  │   │   └── intrinsic_zk_z_K_J.yaml
  │   └── lsst
  │       ├── intrinsic_zk__K_J.yaml
  │       ├── intrinsic_zk_g_K_J.yaml
  │       ├── intrinsic_zk_i_K_J.yaml
  │       ├── intrinsic_zk_r_K_J.yaml
  │       ├── intrinsic_zk_u_K_J.yaml
  │       ├── intrinsic_zk_y_K_J.yaml
  │       └── intrinsic_zk_z_K_J.yaml
  ├── sensitivity_matrix
  │   ├── comcam_sensitivity_dz_K_J_Z.yaml
  │   └── lsst_sensitivity_dz_K_J_Z.yaml
  ├── y2
  │   ├── comcam_y2.yaml
  │   ├── lsst_gaussian_quadrature_y2.yaml
  │   ├── lsst_y2.yaml
  │   └── lsstfam_y2.yaml
  └── state0inDof.yaml

Basically, a valid configuration directory will contain, at the very minimum;

  - one ``M1M3`` directory,
  - one ``M2`` directory,
  - one ``configurations`` directory,
  - one ``image_quality_weights`` directory,
  - one ``sample_points`` directory,
  - one ``intrinsic zernikes`` directory,
  - one ``sensitivity_matrix`` directory,
  - one ``y2`` directory,
  - one ``state0inDof.yaml`` file,

The name of the instrument directory is used by the :py:class:`OFCData <lsst.ts.ofc.OFCData>` to determine where to read the instrument-related configuration files.
This is done by the input argument when creating the class, e.g.;

.. code-block:: python

  ofc_data = OFCData("lsst", "./ofc_config_dir/")

Will read the instrument mode files from the ``lsst`` files and directories.

Which means it defines the following instruments by default:

  - comcam: Commissioning Camera.
  - lsst: LSST Camera.

And the following instrument modes:
  - comcam: Commissioning Camera full array mode.
  - lsst: LSST Camera corner wavefront sensing mode.
  - lsstfam: LSST Camera full array mode.

For each instrument the following files must be defined:

  - ``configurations/instrument.yaml``; configuration file for the instrument used to evaluate double zernike objects.
    It is a yaml file used to define the pupil and obscuration inner and outer radius.
  - ``intrinsic_zk_<filter_name>_X_Y.yaml``; intrinsic Zernike coefficients for the ``filter_name`` filter.
    This is a 2-dimension array with 31 x 23 elements.
    It corresponds to the double zernike intrinsic zernikes
    The first dimension is number of terms of Zernike polynomials across the pupil.
    The second dimension is number of terms of Zernike polynomial across the field (Z1-Z22).
    Note that the first element in the second dimension is meaningless, corresponds to Z0.
    The unit is (Zk in um)/ (wavelength in um).
    The filter names must match the values in :py:attr:`BaseOFCData.eff_wavelength <lsst.ts.ofc.OFCData.eff_wavelength>`.
    If you want to provide a custom set of filters, make sure you update the dictionary with the appropriate information.
  - ``instrument_sensitivity_dz_X_Y_Z.yaml``; double zernike sensitivity matrix.
    These files defines a 3-dimension array with X x Y x Z elements.
    They are the double zernike sensitivity matrix.
    The first dimension is number of terms of Zernike polynomials across the pupil.
    The second dimension is number of terms of Zernike polynomial across the field.
    The third dimension is the number of degrees of freedom (DOF).
    The DOF are (1) M2 dz, dx, dy in um, (2) M2 rx, ry in arcsec, (3) Cam dz, dx, dy in um, (4) Cam rx, ry in arcsec, (5) 20 M1M3 bending mode in um,  (6) 20 M2 bending mode in um.

For each instrument mode the following files must be defined:

  - ``instrument_weights.yaml``; weighting ratio of image quality used in the Q matrix in cost function.
  - ``instrument_points.yaml``; mapping between the sensor name and sensor field position.
  - ``instrument_y2.yaml``; the wavefront error correction between the central raft and corner wavefront sensor.

The directory must also include the following files that are shared among different instruments:
  - ``state0inDof.yaml``: initial state of the optics in the basis of DOF.

Additionally, the directory includes three additional files corresponding to the Gaussian Quadrature Points and Weights used to compute the image quality when using lsst instrument. 
  - ``lsst_gaussian_quadrature_weights.yaml``; weighting ratio of image quality used in the Q matrix in cost function.
  - ``lsst_gaussian_quadrature_points.yaml``; mapping between the sensor name and sensor field position.
  - ``lsst_gaussian_quadrature_y2.yaml``; the wavefront error correction between the central raft and corner wavefront sensor.

Finally, there are also different configurations for the controller. These configurations can be modified to try different gains.
  - ``pid_controller.yaml``; configuration file for the PID controller.
  - ``oic_controller.yaml``; configuration file for the OIC controller.