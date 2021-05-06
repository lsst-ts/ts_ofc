
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

Important classes:

* :py:class:`BaseOFCData <lsst.ts.ofc.ofc_data.BaseOFCData>` a `python data class`_ that contains the static data for the ofc operation.
* :py:class:`OFCData <lsst.ts.ofc.ofc_data.OFCData>` a data container class that inherits ``BaseOFCData`` and handles the dynamic data for ofc operations.
  This includes reading and storing data from files and higher level data manipulation.
* :py:class:`StateEstimator <lsst.ts.ofc.StateEstimator>` contains facilities to estimate the state of the system.
* :py:class:`OFCController <lsst.ts.ofc.OFCController>` calculates the degrees of freedom (DoF) offset by minimizing the cost function.
* :py:class:`OFC <lsst.ts.ofc.OFC>` is the main class of the system, responsible for managing the conversion of wavefront errors into corrections.

.. _python data class: https://docs.python.org/3.8/library/dataclasses.html

.. uml:: ../uml/ofc_class.uml
    :caption: OFC Class diagram.


.. _lsst.ts.ofc-pyapi:

Control Algorithm
=================

.. toctree::
    :glob:

    control-algorithm/*

Python API reference
====================

.. automodapi:: lsst.ts.ofc
    :no-inheritance-diagram:

.. automodapi:: lsst.ts.ofc.ofc_data
    :no-inheritance-diagram:

.. automodapi:: lsst.ts.ofc.utils
    :no-inheritance-diagram:

.. _lsst.ts.ofc-contributing:

Contributing
============

``lsst.ts.ofc`` is developed at https://github.com/lsst-ts/ts_ofc.

References
==========

1. Angeli, George Z. et al., Real time wavefront control system for the Large Synoptic Survey Telescope (LSST), Proc. SPIE 9150, Modeling, Systems Engineering, and Project Management for Astronomy VI, 91500H (2014). <https://doi.org/10.1117/12.2055390>
2. Angeli, George Z. et al., An integrated modeling framework for the Large Synoptic Survey Telescope (LSST), Proc. SPIE 9911, Modeling, Systems Engineering, and Project Management for Astronomy VI, 991118 (2016). <https://doi.org/10.1117/12.2234078>
3. Angeli, George Z. and Xin, Bo, Normalized Point Source Sensitivity for LSST, document-17242 (2016). <https://docushare.lsst.org/docushare/dsweb/Get/Document-17242>
4. [Details of optical state estimation and control algorithms.](https://confluence.lsstcorp.org/display/LTS/Control+Algorithm+in+Optical+Feedback+Control)
5. [Subsystem coordinate transformation.](https://confluence.lsstcorp.org/display/LTS/Subsystem+Coordinate+Transformation)
6. [Camera rotation and degree of freedom.](https://confluence.lsstcorp.org/display/LTS/Camera+Rotation+and+Degree+of+Freedom)
