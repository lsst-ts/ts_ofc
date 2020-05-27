.. py:currentmodule:: lsst.ts.ofc

.. _lsst.ts.ofc-version_history:

##################
Version History
##################

.. _lsst.ts.ofc-1.3.1:

-------------
1.3.1
-------------

Reformat the code by black. Add the black check to .githooks. Ignore flake8 check of E203 ans W503 for the black. Use the sims_w_2020_21. Fix the hexapod rotation matrix.

.. _lsst.ts.ofc-1.3.0:

-------------
1.3.0
-------------

Adds parameter to specify values of state 0 DoF (M2 & Camera hexapod positions, M1M3 & M2 bending modes).

.. _lsst.ts.ofc-1.2.6:

-------------
1.2.6
-------------

Use sims_w_2020_15. Update the bending mode files. Update optiPSSN.yaml for the new penality values. Update OptCtrlDataDecorator class to use BendModeToForce to get the bending mode. Update the rotation matrix of mirror in CamRot class. Remove the bending mode transformation in SubSysAdap class.

.. _lsst.ts.ofc-1.2.5:

-------------
1.2.5
-------------

Use sims_w_2020_14.

.. _lsst.ts.ofc-1.2.4:

-------------
1.2.4
-------------

Use sims_w_2020_04.

.. _lsst.ts.ofc-1.2.3:

-------------
1.2.3
-------------

Use sims_w_2019_50.

.. _lsst.ts.ofc-1.2.2:

-------------
1.2.2
-------------

Use sims_w_2019_38.

.. _lsst.ts.ofc-1.2.1:

-------------
1.2.1
-------------

Use sims_w_2019_31 and the latest ts_wep version. Remove the conda package installation in Jenkinsfile. Update the permission of workspace after the unit test.

.. _lsst.ts.ofc-1.2.0:

-------------
1.2.0
-------------

Use sims_w_2019_29 and the latest ts_wep version. Add the getZtaac() in OFCCalculation class.

.. _lsst.ts.ofc-1.1.9:

-------------
1.1.9
-------------

Use sims_w_2019_24. Add the dependency of ts_wep in the table file. Move the SensorWavefronError class to ts_wep.

.. _lsst.ts.ofc-1.1.8:

-------------
1.1.8
-------------

Use sims_w_2019_20.

.. _lsst.ts.ofc-1.1.7:

-------------
1.1.7
-------------

Depend on the ts_wep and support the documenteer. Use sims_w_2019_18.

.. _lsst.ts.ofc-1.2.4:

-------------
1.1.6
-------------

Add the unit tests of control interface classes and fix the minor errors. Add the Shack-Hartmann and CMOS cameras.

.. _lsst.ts.ofc-1.1.5:

-------------
1.1.5
-------------

Add the classes to translate the Zemax coordinate to subsystem's coordinate and vice versa.

.. _lsst.ts.ofc-1.1.4:

-------------
1.1.4
-------------

Use the eups as the package manager and yaml configuration file format.

.. _lsst.ts.ofc-1.1.3:

-------------
1.1.3
-------------

Add the get functions of state in OFCCalculation class.

.. _lsst.ts.ofc-1.1.2:

-------------
1.1.2
-------------

Fix the interface class of M2HexapodCorrection. Rename the HexapodCorrection class to CameraHexapodCorrection.

.. _lsst.ts.ofc-1.1.1:

-------------
1.1.1
-------------

Add the interface to MTAOS in ctrlIntf module.

.. _lsst.ts.ofc-1.0.1:

-------------
1.0.1
-------------

Reuse the FilterType Enum from ts_tcs_wep.

.. _lsst.ts.ofc-1.0.0:

-------------
1.0.0
-------------

Finish the OFC with the support of algorithm study in Python.
