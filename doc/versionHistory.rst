.. py:currentmodule:: lsst.ts.ofc

.. _lsst.ts.ofc-version_history:

##################
Version History
##################

.. _lsst.ts.ofc-3.2.0:

v3.2.0
======

* Add PIDController as alternative control strategy.
* Move current control strategy to OICController (optimal integral controller).
* Add PID option to OICController output.

.. _lsst.ts.ofc-3.1.3:

v3.1.3
======

* Update to use ts_jenkins_shared_library.

.. _lsst.ts.ofc-3.1.2:

v3.1.2
======

* Move class diagrams to mermaid from plantUML.

.. _lsst.ts.ofc-3.1.1:

v3.1.1
======

* Update Jenkins to do daily and weekly builds.

.. _lsst.ts.ofc-3.1.0:

v3.1.0
======

* Update sensitivity matrix and intrinsic zernikes up to zk 28.
* Add zn_selected to select the zernikes to be used.
* Updated alpha values for image quality matrix.

.. _lsst.ts.ofc-3.0.2:

v3.0.2
======

* Update the version of ts-conda-build to 0.4 in the conda recipe.

.. _lsst.ts.ofc-3.0.1:

v3.0.1
======

* Removed Zemax Coordinate System, which is substituted by the Camera Coordinate System.
* Updated the bending modes used to the new uncorrupted bending modes.
* Updated sensitivity matrix and intrinsic zernikes for the new coordinate system and new bending modes.
* Removed old unused test data.

.. _lsst.ts.ofc-3.0.0:

v3.0.0
======

Major refactor of ofc code to allow camera rotation.

* Added derotation of ts_wep zernike estimates to deal with rotation of the sensor.
* Added ability to evaluate sensitivity matrix and intrinsic zernikes at the rotated field position.
    * Added double zernikes sensitivity matrix for lsst and comcam.
    * Added double zernikes intrinsic zernikes for lsst and comcam.
* Policy folder was simplified since lsstfam and lsst share all double zernike files.
* Added scripts to generate sensitivity matrix and intrinsic files from batoid package.

.. _lsst.ts.ofc-2.1.1:

v2.1.1
======

* Update pre-commit hooks with ruff.

.. _lsst.ts.ofc-2.1.0:

v2.1.0
======

* Update setup configuration files, remove flake8.

.. _lsst.ts.ofc-2.0.9:

v2.0.9
======

* Create additional default factories for BaseOFCData.

.. _lsst.ts.ofc-2.0.8:

v2.0.8
======

* Run black v23.1.0.
* Update Jenkinsfile.

.. _lsst.ts.ofc-2.0.7:

v2.0.7
======

* Update Jenkinsfile, posting to aos-builds.

.. _lsst.ts.ofc-2.0.6:

v2.0.6
======

* Added documentation link to the README.

.. _lsst.ts.ofc-2.0.5:

v2.0.5
======

* Format with Black v22.3.0.

.. _lsst.ts.ofc-2.0.4:

v2.0.4
======

* Update LSSTCam sensor names.

.. _lsst.ts.ofc-2.0.3:

v2.0.3
======

* Fix `setup.cfg` to support conda versioning.

.. _lsst.ts.ofc-2.0.2:

v2.0.2
======

* ``OFC.get_correction()`` should give the aggregated degree of freedom (DOF).
* Remove the out-of-date documents: *content.rst*, *ctrlIntfClass.uml*, and *ofcClass.uml*.

.. _lsst.ts.ofc-2.0.1:

v2.0.1
======

* Put the **delta** in ``BaseOFCData`` to be property.

.. _lsst.ts.ofc-2.0.0:

v2.0.0
======

Major refactor of ofc code.

* The code was reorganized so that the main user-interface class (previously ``OFCCalculation``, now just ``OFC``) is at the top level of the package.
* The ``OFC`` class is no longer subclassed for the different instruments, since the behavior was the same in all cases.
* Document the control algorithm for OFC in rst from Confluence
* Document the camera rotation degree of freedom in rst from Confluence
* General improvements in documentation.

Data handling
-------------

All data is now handled by a two container classes, ``BaseOFCData`` and ``OFCData``, which is shared between all the other classes that require data access.
Most of the data is defined in-line, instead of reading them from files.
The data that is read from files are the ones for the instruments.
This is handled in the background when the user sets the "name" attribute in an instance of OFCData.
All data is read at once and stored in memory to avoid unnecessary IO during computation.
In the future we may consider adding more data protection and data parsing capabilities, but I think this will work fine for this first iteration.

Corrections
-----------

Corrections is now handled by a single class.

Removed WEP dependency
----------------------

OFC now does not depend on WEP anymore.
The dependency was mostly on enumerations for filter names and other things that mapped to string/filenames.
These where all replaced by true strings.
The advantage is that OFC is no longer tied to that particular use cases, if the user can provide configuration files that matches the input they can use it with WEP without any code changes.

Controller and State Estimator
------------------------------

The core classes where previously called `OptCtrl` and `OptStateEsti`.
They were renamed `OFCController` and `StateEstimator`.


.. _lsst.ts.ofc-1.3.7:

v1.3.7
======

* Build and upload documentation as part of the CI job.
* Use develop-env image for the CI job, due to the need of java to build the documentation.
* Disable concurrent builds.
* Improve error message in `OptStateEsti._getMatA`

.. _lsst.ts.ofc-1.3.6:

v1.3.6
======

* Unify the line ending to LF.

.. _lsst.ts.ofc-1.3.5:

v1.3.5
======

* Use the latest **ts_wep** that removes the dependency of ``sims`` package.

.. _lsst.ts.ofc-1.3.4:

v1.3.4
======

* Use the ``sims_w_2020_38``.

.. _lsst.ts.ofc-1.3.3:

v1.3.3
======

* Use the ``sims_w_2020_36``.
* Support the LSST full-array mode (FAM) by adding the **OFCCalculationOfLsstFam** class.

.. _lsst.ts.ofc-1.3.2:

v1.3.2
======

* Update the sensitivity matrix and M2 force file.
* This unifies the corrdinate system of M1M3 and M2 in FEA model.
* Test the ``sims_w_2020_28``.

.. _lsst.ts.ofc-1.3.1:

v1.3.1
======

* Reformat the code by ``black``.
* Add the ``black`` check to ``.githooks``.
* Ignore ``flake8`` check of E203 ans W503 for the ``black``.
* Use the ``sims_w_2020_21``.
* Fix the hexapod rotation matrix.

.. _lsst.ts.ofc-1.3.0:

v1.3.0
======

* Adds parameter to specify values of state 0 DoF (M2 & Camera hexapod positions, M1M3 & M2 bending modes).

.. _lsst.ts.ofc-1.2.6:

v1.2.6
======

* Use ``sims_w_2020_15``.
* Update the bending mode files.
* Update **optiPSSN.yaml** for the new penality values.
* Update **OptCtrlDataDecorator** class to use **BendModeToForce** to get the bending mode.
* Update the rotation matrix of mirror in **CamRot** class.
* Remove the bending mode transformation in **SubSysAdap** class.

.. _lsst.ts.ofc-1.2.5:

v1.2.5
======

* Use ``sims_w_2020_14``.

.. _lsst.ts.ofc-1.2.4:

v1.2.4
======

* Use ``sims_w_2020_04``.

.. _lsst.ts.ofc-1.2.3:

v1.2.3
======

* Use ``sims_w_2019_50``.

.. _lsst.ts.ofc-1.2.2:

v1.2.2
======

* Use ``sims_w_2019_38``.

.. _lsst.ts.ofc-1.2.1:

v1.2.1
======

* Use ``sims_w_2019_31`` and the latest **ts_wep** version.
* Remove the ``conda`` package installation in **Jenkinsfile**.
* Update the permission of workspace after the unit test.

.. _lsst.ts.ofc-1.2.0:

v1.2.0
======

* Use ``sims_w_2019_29`` and the latest **ts_wep** version.
* Add the ``getZtaac()`` in **OFCCalculation** class.

.. _lsst.ts.ofc-1.1.9:

v1.1.9
======

* Use ``sims_w_2019_24``.
* Add the dependency of **ts_wep** in the table file.
* Move the **SensorWavefronError** class to **ts_wep**.

.. _lsst.ts.ofc-1.1.8:

v1.1.8
======

* Use ``sims_w_2019_20``.

.. _lsst.ts.ofc-1.1.7:

v1.1.7
======

* Depend on the **ts_wep** and support the ``documenteer``.
* Use ``sims_w_2019_18``.

.. _lsst.ts.ofc-1.1.6:

v1.1.6
======

* Add the unit tests of control interface classes and fix the minor errors.
* Add the Shack-Hartmann and CMOS cameras.

.. _lsst.ts.ofc-1.1.5:

v1.1.5
======

* Add the classes to translate the Zemax coordinate to subsystem's coordinate and vice versa.

.. _lsst.ts.ofc-1.1.4:

v1.1.4
======

* Use the ``eups`` as the package manager and ``yaml`` configuration file format.

.. _lsst.ts.ofc-1.1.3:

v1.1.3
======

* Add the get functions of state in **OFCCalculation** class.

.. _lsst.ts.ofc-1.1.2:

v1.1.2
======

* Fix the interface class of **M2HexapodCorrection**.
* Rename the **HexapodCorrection** class to **CameraHexapodCorrection**.

.. _lsst.ts.ofc-1.1.1:

v1.1.1
======

* Add the interface to **MTAOS** in ``ctrlIntf`` module.

.. _lsst.ts.ofc-1.0.1:

v1.0.1
======

* Reuse the **FilterType** Enum from **ts_tcs_wep**.

.. _lsst.ts.ofc-1.0.0:

v1.0.0
======

* Finish the OFC with the support of algorithm study in Python.
