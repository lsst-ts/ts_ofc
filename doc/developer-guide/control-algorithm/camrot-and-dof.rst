#####################################
Camera Rotation and Degree of Freedom
#####################################

This document explains the relationship between the camera rotation and degree of freedom (DOF).
When the wavefront sensor takes the images, the rotation angle (:math:`\theta`) might not be zero and the calculated DOF needs to compensate for this, which means to rotate the DOF back to the reference plane (:math:`\theta = 0`).
It is the similar case for the hexapod position

.. _Mirror Bending Mode:

Mirror Bending Mode
===================
If the (x, y) coordinate plane rotates by an angle :math:`\theta` in the counter-clockwise directon, the new coordinate system (x', y') is:

.. math::
    
    \begin{bmatrix}
    x' \\
    y'
    \end{bmatrix}
    =
    \begin{bmatrix}
    cos(\theta) & sin(\theta) \\
    -sin(\theta) & cos(\theta)
    \end{bmatrix}
    \begin{bmatrix}
    x \\
    y
    \end{bmatrix}.

Since the measurement is on the (x', y') plane, the real value (x, y) should be:

.. math::

    \begin{bmatrix}
    x \\
    y
    \end{bmatrix}
    =
    \begin{bmatrix}
    cos(\theta) & -sin(\theta) \\
    sin(\theta) & cos(\theta)
    \end{bmatrix}
    \begin{bmatrix}
    x' \\
    y'
    \end{bmatrix}.

Or rewrite the above formula as :math:`\vec{x} = \textbf{R}\vec{x}'`.
The rotation matrix for 20 bending modes is :math:`\text{diag}([\textbf{R}, 1, \textbf{R}, \textbf{R}, \textbf{R}, 1, \textbf{R}, \textbf{R}, \textbf{R}, \textbf{R}])`

Hexapod Position
================
For the camera rotation consider the figure below:

.. image:: /images/hexa1.png

The rotation angle :math:`\theta'` on the plane 1 transforms to the angle :math:`\theta` on the plane 2 with a tilt rotation, which is tilt-:math:`x'` here.
The plane 2 is parallel to the plane 3, which is the face of hexapod.
Basically, the first step is to get the relationship between :math:`\theta'` and :math:`\theta`.
Then, do the rotation between x, y-plane and x', y' plane.

The rotation matrix between x, y-plane and x', y'-plane is:

.. math::

    \begin{bmatrix}
    z \\
    x \\
    y \\
    r_{x} \\
    r_{y}
    \end{bmatrix}
    =
    \begin{bmatrix}
    1 & 0 & 0 & 0 & 0 \\
    0 & \cos(\theta) & -\sin(\theta) & 0 & 0 \\
    0 & \sin(\theta) & \cos(\theta) & 0 & 0 \\
    0 & 0 & 0 & \cos(\theta) & -\sin(\theta) \\
    0 & 0 & 0 & \sin(\theta) & \cos(\theta)
    \end{bmatrix}
    \begin{bmatrix}
    z' \\
    x' \\
    y' \\
    r_{x}' \\
    r_{y}'
    \end{bmatrix}.

For the camera hexapod, :math:`\theta'` equals :math:`\theta`.
For the M2 hexapod, consider the following figure:

.. image:: /images/hexa2.png

It is clear that the rotation angle :math:`\theta'` on the x', y'-plane will be the same as the rotation angle :math:`\theta` on the x, y-plane if there is no tilt angle difference (e.g. :math:`r_{x}' = r_{x}` and :math:`r_{y}' = r_{y}`).
It is noted that :math:`r_{z} = r_{z}' = 0`.
In other words, :math:`\theta = f(\theta', \Delta r_{x}, \Delta r_{y})` is a function of :math:`\theta'`, :math:`\Delta r_{x} = r_{x, \text{Cam}}'-r_{x, \text{M2}}`, and :math:`\Delta r_{y} = r_{y, \text{Cam}}'-r_{y, \text{M2}}`.

Based on `Rodrigues' rotation formula <https://en.wikipedia.org/wiki/Rodrigues%27_rotation_formula>`_ if a vector (:math:`\vec{v}`) in :math:`\mathbb{R}^{3}` is rotated by an angle :math:`\theta{\text{r}}` about a unit vector :math:`\hat{r}` according to the right-hand rule, the rotated vector (:math:`\vec{v}'`) is:

.. math::

    \vec{v}' = \vec{v}\cos(\theta_{\text{r}}) + (\hat{r}\times\vec{v})\sin(\theta_{\text{r}}) + \hat{r}(\hat{r}\cdot\vec{v})(1-\cos(\theta_{\text{r}})).

Set :math:`\vec{v} = \cos(\theta)\hat{x} + \sin(\theta)\hat{y}` and rotate :math:`\vec{v}` by an angle :math:`\alpha` about the axis :math:`\hat{x}`, we have:

.. math::

    \begin{align*}
    \vec{v}' &= \vec{v}\cos(\alpha) + (\hat{x}\times\vec{v})\sin(\alpha) + \hat{x}(\hat{x}\cdot\vec{v})(1-\cos(\alpha)) \\
    &= \cos(\theta)\hat{x} + \sin(\theta)\cos(\alpha)\hat{y} + \sin(\theta)\sin(\alpha)\hat{z}.
    \end{align*}

Rotate the :math:`\vec{v}'` by an angle :math:`\beta` about the axis :math:`\hat{y}`, we have:

.. math::

    \begin{align*}
    \vec{v}'' &= \vec{v}'\cos(\beta) + (\hat{y}\times\vec{v}')\sin(\beta) + \hat{y}(\hat{y}\cdot\vec{v}')(1-\cos(\beta)) \\
    &= (\cos(\theta)\cos(\beta) + \sin(\theta)\sin(\alpha)\sin(\beta) )\hat{x} + \sin(\theta)\cos(\alpha)\hat{y} + ( \sin(\theta)\sin(\alpha)\cos(\beta) - \cos(\theta)\sin(\beta) )\hat{z}.
    \end{align*}

To get the angle :math:`\theta'`, we use:

.. math::

    \begin{align*}
    \tan(\theta') &= \frac{\vec{v}''\cdot\hat{y}}{\vec{v}''\cdot\hat{x}} \\
    &= \frac{\sin(\theta)\cos(\alpha)}{\cos(\theta)\cos(\beta) + \sin(\theta)\sin(\alpha)\sin(\beta)} \\
    &= \frac{\tan(\theta)\cos(\alpha)}{\cos(\beta) + \tan(\theta)\sin(\alpha)\sin(\beta)}.
    \end{align*}

Since the tilt angles are small based on LTS-206, assume :math:`\alpha = \delta_{1}` and :math:`\beta = \delta_{2}` with :math:`\delta{1}, \delta_{2} \ll 1`, we have:

.. math::

    \begin{align*}
    \tan(\theta') &\approx \frac{\tan(\theta)\cdot(1-\delta_{1})}{1-\delta_{2}+\tan(\theta)\cdot\delta_{1}\cdot\delta_{2}} \\
    &\approx \tan(\theta)\cdot(1-\delta_{1}+\delta_{2}).
    \end{align*}

If we consider the tilt angle difference between the camera rotator and camera hexapod, the above equation can be rewritten as

.. math::

    \tan(\theta') \approx \tan(\theta)\cdot(1-\delta_{1}-\delta_{1,\text{ref}}+\delta_{2}+\delta_{2,\text{ref}}),

where :math:`\delta_{1/2,ref}` is the tilt angle difference between the camera rotator and hexapod about :math:`x/y`.
The details of the above calculation can follow: `cam rot cal.pdf <https://confluence.lsstcorp.org/download/attachments/77991830/cam%20rot%20cal.pdf?version=1&modificationDate=1530525677000&api=v2>`_.
To see the affection of rotation angle, assume :math:`\delta_{2} = \delta_{1,\text{ref}} = \delta_{2,\text{ref}} = 0`, we can plot the rotated angle as the following:

.. image:: /images/camRot.jpg

It is clear that the change of angle is small (:math:`< 0.2^{\circ}`) since the range of the tilt angle is :math:`\pm 0.17^{\circ}` according to the LTS-206.
It is noted that in the real implementation, the reference of tilt angle is not considered (:math:`\delta_{1/2,\text{ref}} = 0`) because it is believed that the values should be in the noise range.

Since the tilt angles between the camera and M1M3 are different, the above angle correction applies to M1M3 also.
That means the rotation angle on the :ref:`Mirror Bending Mode`, is the corrected camera angle with :math:`\Delta r_{x} = r_{x, \text{Cam}}'-r_{x, \text{M1M3}}` and :math:`\Delta r_{y} = r_{y, \text{Cam}}'-r_{y, \text{M1M3}}.`
The rotation angle can be simplified further to be :math:`\Delta r_{x} = r_{x, text{Cam}}'` and :math:`\Delta r_{y} = r_{y, \text{Cam}}'` because the relative coordinate system is used with the M1M3 as the reference point.
And it is the similar correction for M2 bending mode.

\* Some studies based on the affine transformation and Euler rotation are `Coordinate Transformation.nb <https://confluence.lsstcorp.org/download/attachments/77991830/Coordinate%20Transformation.nb?version=1&modificationDate=1531750704000&api=v2>`_, `Coordinate Transformation.pdf <https://confluence.lsstcorp.org/download/attachments/77991830/Coordinate%20Transformation.pdf?version=1&modificationDate=1531750720000&api=v2>`_, `Coordinate Transformation 2.nb <https://confluence.lsstcorp.org/download/attachments/77991830/Coordinate%20Transformation%202.nb?version=1&modificationDate=1531750745000&api=v2>`_, and `Coordinate Transformation 2.pdf <https://confluence.lsstcorp.org/download/attachments/77991830/Coordinate%20Transformation%202.pdf?version=1&modificationDate=1531750766000&api=v2>`_.

#####################################
Camera Rotation with Double Zernikes
#####################################

In this mode we use the double zernike sensitivity matrix and the DoubleZernike class in galsim, to compute the sensitivity matrix at the rotated angle. 
This allows us to remove the degree of freedom rotatione explained above. 