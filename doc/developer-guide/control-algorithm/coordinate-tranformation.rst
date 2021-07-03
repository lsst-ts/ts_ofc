###################################
Subsystem Coordinate Transformation
###################################

This document explains the coordinate transformation between ZEMAX and subsystems contain the hexapod and mirror.
The finite element analysis (FEA) model of system engineer (SE) and M1M3 mechanical team use different coordinate systems (M2 to M1M3 vs. M1M3 to M2), the transformation between each other will be clarified in this document.
The relationship between ZEMAX and hexapod coordinate system will be discussed also.

M1M3 Mirror
===========
The layouts of 156 actuator IDs for two FEA models are shown in the following:

.. image:: /images/M1M3\ ID.jpg

.. image:: /images/SE\ ID.jpg

It is clear that the position of actuator 101 is in +x for M1M3 mechanical team but -x for SE team.
This is because +z is defined to be from M1M3 to M2 in M1M3 mechanical team but this direction is -z in SE team.
The M1M3 uses the optical coordinate system defined in LTS-136.
For both teams, the right hand rule is applied for x and y directions.
The figure below shows this:

.. image:: /images/Untitled.png

The detail of coordinate system defined by M1M3 mechanical team is at `4.6.3 M1M3 / Mirror Support Pneumatic Actuators <https://confluence.lsstcorp.org/pages/viewpage.action?pageId=47220348>`_ and `M1M3 FEA <https://docushare.lsstcorp.org/docushare/dsweb/View/Collection-5087/Document-25194>`_.
The data of M1M3 FEA is also used for the following rotation matrix analysis of bending mode.

The active optics system (AOS) uses the first 20 bending modes (or DOFs) based on the elastic theory with FEA.
The following figure compares the calculated bending modes by two teams:

.. image:: /images/std.jpg

It is clear that the two teams have similar 156 actuator forces for each bending mode.
Most bending modes have related pairs (e.g. mode 1 and 2) except mode 3 and 12, which are related to the defocus and primary spherical terms.
Actually, we can see they correspond to `Zernike Polynomials <https://en.wikipedia.org/wiki/Zernike_polynomials>`_ directly.

Since the optical feedback control (OFC) sends the actuator forces to mirror controllers (LTS-AOCS-REQ-0004, LTS-186 v2), the easiest way is to multiply the 156 actuator forces by -1 after transforming the estimated M1M3 bending mode offset to force based on SE's FEA model.
However, the LTS-88 v5 has the requirement that mirror controller shall accept the AOS bending mode offset (LTS-MSS-REQ-0089), which means the rotation of bending modes between two FEA models is necessary.

To get the rotation matrix of bending modes, a straight-forward way is to multiply the actuator forces by -1 in SE FEA model and compares the result with the FEA model by M1M3 mechanical team.
For example, from the figure below (note: x-axis is flipped in the right figure to align the actuator IDs of two coordinate systems), it is easy to know the bending mode 1 is the same for SE and M1M3 mechanical teams.

.. image:: /images/M1M3b1.jpg

.. image:: /images/SEb1.jpg

The rotation matrix of 20 bending modes from SE team to M1M3 mechanical team is listed below:

.. math::

    \begin{bmatrix}
    \vec{1}' \\
    \vec{2}'
    \end{bmatrix}_{\text{M1M3}}
    =
    \begin{bmatrix}
    1 & 0 \\
    0 & -1
    \end{bmatrix}
    \begin{bmatrix}
    \vec{1} \\
    \vec{2}
    \end{bmatrix}_{\text{SE}}

.. math::

    \begin{bmatrix}
    \vec{3}'
    \end{bmatrix}_{\text{M1M3}}
    =
    \begin{bmatrix}
    1 
    \end{bmatrix}
    \begin{bmatrix}
    \vec{3}
    \end{bmatrix}_{\text{SE}}

.. math::

    \begin{bmatrix}
    \vec{4}' \\
    \vec{5}'
    \end{bmatrix}_{\text{M1M3}}
    =
    \begin{bmatrix}
    1 & 0 \\
    0 & 1
    \end{bmatrix}
    \begin{bmatrix}
    \vec{4} \\
    \vec{5}
    \end{bmatrix}_{\text{SE}}

.. math::

    \begin{bmatrix}
    \vec{6}' \\
    \vec{7}'
    \end{bmatrix}_{\text{M1M3}}
    =
    \begin{bmatrix}
    -1 & 0 \\
    0 & -1
    \end{bmatrix}
    \begin{bmatrix}
    \vec{6} \\
    \vec{7}
    \end{bmatrix}_{\text{SE}}

.. math::

    \begin{bmatrix}
    \vec{8}' \\
    \vec{9}'
    \end{bmatrix}_{\text{M1M3}}
    =
    \begin{bmatrix}
    -1 & 0 \\
    0 & -1
    \end{bmatrix}
    \begin{bmatrix}
    \vec{8} \\
    \vec{9}
    \end{bmatrix}_{\text{SE}}

.. math::

    \begin{bmatrix}
    \vec{10}' \\
    \vec{11}'
    \end{bmatrix}_{\text{M1M3}}
    =
    \begin{bmatrix}
    1 & 0 \\
    0 & -1
    \end{bmatrix}
    \begin{bmatrix}
    \vec{10} \\
    \vec{11}
    \end{bmatrix}_{\text{SE}}

.. math::

    \begin{bmatrix}
    \vec{13}' \\
    \vec{14}'
    \end{bmatrix}_{\text{M1M3}}
    =
    \begin{bmatrix}
    -1 & 0 \\
    0 & -1
    \end{bmatrix}
    \begin{bmatrix}
    \vec{13} \\
    \vec{14}
    \end{bmatrix}_{\text{SE}}

.. math::

    \begin{bmatrix}
    \vec{15}' \\
    \vec{16}'
    \end{bmatrix}_{\text{M1M3}}
    =
    \begin{bmatrix}
    -1 & 0 \\
    0 & 1
    \end{bmatrix}
    \begin{bmatrix}
    \vec{15} \\
    \vec{16}
    \end{bmatrix}_{\text{SE}}

.. math::

    \begin{bmatrix}
    \vec{17}' \\
    \vec{18}'
    \end{bmatrix}_{\text{M1M3}}
    =
    \begin{bmatrix}
    -1 & 0 \\
    0 & -1
    \end{bmatrix}
    \begin{bmatrix}
    \vec{17} \\
    \vec{18}
    \end{bmatrix}_{\text{SE}}

.. math::

    \begin{bmatrix}
    \vec{19}' \\
    \vec{20}'
    \end{bmatrix}_{\text{M1M3}}
    =
    \begin{bmatrix}
    -1 & 0 \\
    0 & -1
    \end{bmatrix}
    \begin{bmatrix}
    \vec{19} \\
    \vec{20}
    \end{bmatrix}_{\text{SE}}.

M2 Mirror
=========

M2 uses the same coordinate system as M1M3 (optical coordinate system).
The +z actuator force in M1M3 is push and it is pull in M2.

The bending mode file of M2 is copied from M1M3 at this moment.

Hexapod
=======

The hexapod position is :math:`(z, x, y, r_{x}, r_{y})` in SE team and :math:`(x', y', z', r_{x}', r_{y}', r_{z}')` in T&S team.
:math:`x`, :math:`y`, :math:`z`, :math:`x'`, :math:`y'`, and :math:`z'` are in the unit of um.
:math:`r_{x}` and :math:`r_{y}` are in the unit of arcsec.
:math:`r_{x}'`, :math:`r_{y}'`, and :math:`r_{z}'` are in the unit of degree.
The optical coordinate system in T&S team can follow LTS-136.
The hexapod's coordinate system is the same as optical coordinate system as described in LTS-206.

The comparison of coordinate systems between SE and T&S teams is shown below. 
In SE team, :math:`+z` goes from M2 to M1M3; :math:`+y` goes up; and :math:`+x` follows the right-hand rule.
In T&S team, the :math:`z'` axis is positive up when zenith pointing; the :math:`x'` axis is parallel to the elevation axis; and the :math:`y'` axis is by the right-hand rule and is positive up when horizon pointing.

.. image:: /images/coodinate.png

The rotation matrix between two coordinate systems is:

.. math::

    \begin{bmatrix}
    z \\
    x \\
    y \\
    r_{x} \\
    r_{y}
    \end{bmatrix}_{\text{SE}}
    =
    \begin{bmatrix}
    0 & 0 & -1 & 0 & 0 & 0 \\
    -1 & 0 & 0 & 0 & 0 & 0 \\
    0 & 1 & 0 & 0 & 0 & 0 \\
    0 & 0 & 0 & -3600 & 0 & 0 \\
    0 & 0 & 0 & 0 & -3600 & 0
    \end{bmatrix}
    \begin{bmatrix}
    x' \\
    y' \\
    z' \\
    r_{x}' \\
    r_{y}' \\
    r_{z}'
    \end{bmatrix}_{\text{T&S}}.

It is noted that 1 degree equals 3600 arcsec.
The relationship between tilt angles can be proved by the unitary transformation on the rotation matrix operator (e.g. :math:`\textbf{R}_{\text{y}}(\pi)\textbf{R}_{\text{x}}(r_{x})\textbf{R}_{\text{y}}(\pi)^{-1} = \textbf{R}_{\text{x}}(-r_{x})`).