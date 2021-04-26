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

The Optical Feedback Control class is designed to compute corrections for the optical components given a set of wavefront errors for a group of sensors.
From a user perspective a simple use case will involve creating an instance of the ``OFC`` class, generating some wavefront errors and passing that along to obtain the corrections.

The class receives an instance of ``OFCData``, which is a data container class hosting all the data required for the ``OFC`` operations.

One caveat with using the ``OFCData`` is that it needs to read some data from disk.
These operations can take quite a bit of time and may block the process for a significant period of time.
Because this class is supposed to be used by the ``MTAOS`` CSC we need to be able to support loading it
without blocking the asyncio event loop.
This is handled by the ``OFCData`` class in the background, but the user must be aware that the class is not done loading after it is instantiated.
In order to wait for the class to be ready users must ``await`` for the ``start_task`` to complete, similar to what we do with ``salobj.Remote``.

The following is how one would use the ``OFC`` to generate simple corrections from a list of wavefront errors.

.. code-block:: python

  import numpy as np

  from lsst.ts.ofc import OFC, OFCData

  ofc_data = OFCData("lsst")

  # If you are in a jupyter notebook or a context where an event loop is
  # running (e.g. in a CSC) you need to wait for the class to finish loading
  if not ofc_data.start_task.done():
    await ofc_data.start_task

  ofc = OFC(ofc_data)

  # create some data to process:
  wfe = np.zeros((4,19))

  field_idx = np.arange(4)

  # get corrections from ofc
  m2_hex, cam_hex, m1m3, m2 = ofc.calculate_corrections(
      wfe=wfe, field_idx=field_idx, filter_name="", gain=1.0, rot=0.0
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

This is a dictionary that contains the intrinsic wavefront errors for each filter and for each sensor.
In the case above, we used the empty filter.
If you want to check the intrinsic aberrations for no filter simply do:

.. code-block:: python

  ofc_data.intrinsic_zk[""]

You can also check what are the available filters:

.. code-block:: python

  ofc_data.intrinsic_zk.keys()


A simple and useful test to perform is to pass the intrinsic aberrations to ofc, and check that it returns zeros for all the corrections.
This can be done with the following:

.. code-block:: python

  wfe = ofc_data.get_intrinsic_zk(filter_name="")  # Returns intrinsic zk for all sensors

  field_idx = np.arange(wfe.shape[0])

  # get corrections from ofc
  m2_hex, cam_hex, m1m3, m2 = ofc.calculate_corrections(
      wfe=wfe, field_idx=field_idx, filter_name="", gain=1.0, rot=0.0
  )

  # The corrections now should be all zeros

From the intrinsic corrections you can also easily obtain offsets to add aberrations.
This is, for instance, how the ``MTAOS`` addAberration command works:

.. code-block:: python

  wfe = ofc_data.get_intrinsic_zk(filter_name="")  # Returns intrinsic zk for all sensors

  field_idx = np.arange(wfe.shape[0])

  wfe[:,0:1] += 0.1  # add 0.1 um of defocus

  # get corrections from ofc
  m2_hex, cam_hex, m1m3, m2 = ofc.calculate_corrections(
      wfe=wfe, field_idx=field_idx, filter_name="", gain=1.0, rot=0.0
  )

Another very useful exercise is to modify the sensitivity matrix.
For instance, one can disable operations will all components except the Camera Hexapod by doing the following:

.. code-block:: python

  wfe = ofc_data.get_intrinsic_zk(filter_name="")  # Returns intrinsic zk for all sensors

  field_idx = np.arange(wfe.shape[0])

  wfe[:,0:1] += 0.1  # add 0.1 um of defocus

  # Disable all corrections except camera hexapod
  new_dof_mask = dict(
    m2HexPos=np.zeros(5, dtype=bool),
    camHexPos=np.ones(5, dtype=bool),
    M1M3Bend=np.zeros(20, dtype=bool),
    M2Bend=np.zeros(20, dtype=bool),
  )

  ofc.ofc_data.dof_idx = new_dof_mask

  # get corrections from ofc
  m2_hex, cam_hex, m1m3, m2 = ofc.calculate_corrections(
      wfe=wfe, field_idx=field_idx, filter_name="", gain=1.0, rot=0.0
  )

  print(cam_hex)
  # Should print:
  # CorrectionType.POSITION::[ 0.    -0.    -6.271  0.     0.     0.   ]

This should result in only an offset in z-axis for the camera hexapod.
