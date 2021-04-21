.. py:currentmodule:: lsst.ts.ofc

.. _lsst.ts.ofc:

##############
lsst.ts.ofc
##############

This module is used to calculate the aggregated degree of freedom (DOF) for the hexpods and mirrors. The process contains: (1) estimate the optical state in the basis of DOF, (2) estimate the offset of DOF used in the next iteration/ visit, and (3) rotate the DOF based on the camera rotation angle.

.. _lsst.ts.ofc-using:

Using lsst.ts.ofc
====================

.. toctree::
   :maxdepth: 1

Important classes:

* `DataShare` is for the information change used in the algorithms. This class includes the information of indexes of annular Zernike polynomials (zk) and DOF to use.
* `OptStateEstiDataDecorator` adds the functions/ attributes to DataShare class for the parameters needed in the OptStateEsti class.
* `OptCtrlDataDecorator` adds the functions/ attributes to DataShare class for the parameters needed in the OptCtrl class.
* `OptStateEsti` estimates the optical state by the pseudo-inverse method.
* `OptCtrl` calculates the DOF offset by minimizing the cost function.
* `ZTAAC` is a high-level class to integrate the DataShare, OptStateEstiDefault, and OptCtrlDefault classes.
* `CamRot` rotates the calculated DOF offset.
* `BendModeToForce` transforms the bending mode to actuator forces and vice versa.
* `SubSysAdap` transforms the degree of freedom or actuator forces from ZEMAX coordinate to subsystem's coordinate and vice versa.

.. uml:: uml/ofc.uml
    :caption: OFC Class diagram.

Important enums:

* `InstName` defines the type of instrument.
* `DofGroup` defines the type of DOF.

.. _lsst.ts.ofc-pyapi:

Python API reference
====================

.. automodapi:: lsst.ts.ofc
    :no-inheritance-diagram:

.. _lsst.ts.ofc-content:

Content
====================

.. toctree::

   content

.. _lsst.ts.ofc-contributing:

Contributing
============

``lsst.ts.ofc`` is developed at https://github.com/lsst-ts/ts_ofc.

.. _lsst.ts.ofc-version:

Version
====================

.. toctree::

   versionHistory
