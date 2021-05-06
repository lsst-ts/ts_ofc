.. py:currentmodule:: lsst.ts.ofc

.. _lsst.ts.ofc:

##############################
Optical Feedback Control (OFC)
##############################

.. image:: https://img.shields.io/badge/GitHub-ts_ofc-green.svg
    :target: https://github.com/lsst-ts/ts_ofc
.. image:: https://img.shields.io/badge/Jenkins-ts_ofc-green.svg
    :target: https://tssw-ci.lsst.org/job/LSST_Telescope-and-Site/job/ts_ofc/
.. image:: https://img.shields.io/badge/Jira-ts_ofc-green.svg
    :target: https://jira.lsstcorp.org/issues/?jql=labels+%3D+ts_ofc

.. _overview:

Overview
========

The Optical Feedback Control (OFC) main goal is to process wavefront errors and generate corrections for the optical components; M2 Hexapod, Camera Hexapod, M1M3 and M2.

The software is designed to take into account the state of the system and the degree of freedom in order to optimize the control of the system.

The process contains:
  1. estimate the optical state in the basis of the degrees of freedom (DOF),
  2. estimate the offset of DOF used in the next iteration/visit, and
  3. rotate the DOF based on the camera rotation angle.

.. toctree::
    :glob:
    :maxdepth: 1
    
    *

.. _user-documentation:

User Documentation
==================

User-level documentation, found in the link below, is aimed at scientists and engineers wanting to study the conversion of wavefront errors into optical corrections.


.. toctree::
    user-guide/user-guide
    :maxdepth: 1


.. _development-documentation:

Developer Documentation
=======================

This area of documentation focuses on the architecture of the package, its classes, API's, and how to participate to the development of the package.

.. toctree::
    developer-guide/developer-guide
    :maxdepth: 1

.. _lsst.ts.ofc-version:

Version
====================

.. toctree::
   :maxdepth: 1

   versionHistory
