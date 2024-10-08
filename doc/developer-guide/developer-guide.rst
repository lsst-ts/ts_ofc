
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
* :py:class:`SensitivityMatrix <lsst.ts.ofc.SensitivityMatrix>` calculates the sensitivity matrix at the given sensors and camera rotation angle.
* :py:class:`StateEstimator <lsst.ts.ofc.StateEstimator>` contains facilities to estimate the state of the system.
* :py:class:`OICController <lsst.ts.ofc.OICController>` Optimal Integral Controller that calculates the degrees of freedom (DoF) offset by minimizing the cost function.
* :py:class:`PIDController <lsst.ts.ofc.PIDController>` Proportional-Integral-Derivative Controller that calculates the degrees of freedom (DoF) offset with gains.
* :py:class:`OFC <lsst.ts.ofc.OFC>` is the main class of the system, responsible for managing the conversion of wavefront errors into corrections.

.. _python data class: https://docs.python.org/3.8/library/dataclasses.html

.. mermaid:: ../uml/ofc_class.mmd
    :caption: OFC Class diagram.


.. _lsst.ts.ofc-pyapi:

Control Algorithm
=================

.. toctree::
    :glob:

    control-algorithm/*

For more additional details about the algorithm see [Angeli2014]_, [Angeli2016a]_, [Angeli2016b]_, [MegiasHomar2024]_ and [Xin2021]_.

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

.. [Angeli2014] Angeli, George Z. et al., *Real time wavefront control system for the Large Synoptic Survey Telescope (LSST).* `Proc. SPIE 9150, Modeling, Systems Engineering, and Project Management for Astronomy VI, 91500H (2014). <https://doi.org/10.1117/12.2055390>`_

.. [Angeli2016a] Angeli, George Z. et al., *An integrated modeling framework for the Large Synoptic Survey Telescope (LSST).* `Proc. SPIE 9911, Modeling, Systems Engineering, and Project Management for Astronomy VI, 991118 (2016). <https://doi.org/10.1117/12.2234078>`_

.. [Angeli2016b] Angeli, George Z. and Xin, Bo, *Normalized Point Source Sensitivity for LSST.* `document-17242. <https://docushare.lsst.org/docushare/dsweb/Get/Document-17242>`_

.. [MegiasHomar2024] Megias Homar, G., et al., *The Active Optics System on the Vera C. Rubin Observatory: Optimal Control of Degeneracy Among the Large Number of Degrees of Freedom* `arXiv (2024) <https://arxiv.org/abs/2406.04656>`_

.. [Xin2021] Xin, Bo, *SITCOMTN-003: Coordinate Transformations within the Rubin Active Optics System.* `sticomtn-003 <https://sitcomtn-003.lsst.io>`_
