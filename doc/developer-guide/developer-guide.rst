
.. _developer_guide:

##############################################
Optical Feedback Control (OFC) Developer Guide
##############################################

.. image:: https://img.shields.io/badge/GitHub-ts_ofc-green.svg
    :target: https://github.com/lsst-ts/ts_ofc
.. image:: https://img.shields.io/badge/Jenkins-ts_ofc-green.svg
    :target: https://tssw-ci.lsst.org/job/LSST_Telescope-and-Site/job/ts_ofc/
.. image:: https://img.shields.io/badge/Jira-ts_ofc-green.svg
    :target: https://jira.lsstcorp.org/issues/?jql=labels+%3D+ts_ofc

.. _lsst.ts.ofc-using:

Using lsst.ts.ofc
=================

.. toctree::
    :glob:

    *

Important classes:

* ``OFCData`` is the data container class for OFC operations.
  This class stores all data needed by all child classes.
* ``StateEstimator`` contains facilities to estimate the state of the system.
* ``OFCController`` calculates the DOF offset by minimizing the cost function.
* ``OFC`` is the main class of the system, responsible for managing the conversion of wavefront errors into corrections.

.. uml:: ../uml/ofc_class.uml
    :caption: OFC Class diagram.


.. _lsst.ts.ofc-pyapi:

Python API reference
====================

.. automodapi:: lsst.ts.ofc
    :no-inheritance-diagram:

.. _lsst.ts.ofc-contributing:

Contributing
============

``lsst.ts.ofc`` is developed at https://github.com/lsst-ts/ts_ofc.
