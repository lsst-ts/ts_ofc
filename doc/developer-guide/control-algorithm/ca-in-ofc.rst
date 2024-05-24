#############################################
Control Algorithm in Optical Feedback Control
#############################################

The optical feedback control (OFC) estimates the offset (:math:`\vec{u}`) of degree of freedom (DOF) at time :math:`k+1` based on the wavefront error (:math:`\vec{y}_{k}`) at time :math:`k`.
The feedback amplitude is based on the gain (:math:`g`).
The first step is to evaluate the optical state (:math:`\vec{x}_{k}`) at time :math:`k` in the basis of DOF.
The second step is to evaluate :math:`\vec{u}`.
The final step is to decide the feedback amplitude based on :math:`g`.

The optical state is defined as:

.. math:: 

    \vec{y}_{k} = \textbf{A}\vec{x}_{k} + \vec{y}_{2} + \vec{y}_{\text{c}}(\ell).

:math:`\textbf{A}` is a subset of the sensitivity matrix :math:`\textbf{M}` that is a three-dimension matrix.
For each element :math:`\textbf{M}_{ijk}`, :math:`i` is in the basis of optical field (:math:`\mathbb{O}`), :math:`j` is in the basis of Zernike polynomial(:math:`\mathbb{Z}`), and :math:`k` is in the basis of DOF(:math:`\mathbb{D}`).
:math:`\textbf{A}` equals :math:`[\textbf{M}_1, \textbf{M}_2, \cdots, \textbf{M}_n]^{T}`, where :math:`n\in\mathbb{O}` is the interested optical field point and each element :math:`\textbf{M}_{n, jk}` in :math:`\textbf{M}_{n}` is :math:`\textbf{M}_{njk}` actually.
:math:`\vec{y}_{2}` is the wavefront error correction between the central raft and corner wavefront sensor.
:math:`\vec{y}_{\text{c}}(\ell)` is the intrinsic wavefront error from telescope optical design as a function of filter band (:math:`\ell\in\{\text{u}, \text{g}, \text{r}, \text{i}, \text{z}, \text{y}\}`).
:math:`\vec{y}_{\text{c}}` equals :math:`[\vec{y}_{\text{c},1}, \vec{y}_{\text{c},2}, \cdots,\vec{y}_{\text{c},n}]^{T}` where :math:`n\in\mathbb{O}`.

The pseudo-inverse method is a straight-forward way to solve this over-determined system.
The solution is:

.. math::

    \vec{x}_{k} = \text{pinv}(\textbf{A})(\vec{y}_{k}-\vec{y}_{2}-\vec{y}_{c}(l)),

where :math:`\vec{x}_{k}` is the least norm solution of optical state.

To evaluate :math:`\vec{u}`, the cost function (:math:`J(\vec{u})`) at time :math:`k+1` is defined to be:

.. math::

    J(\vec{u}) = \int_{\sigma \in \mathbb{O}} \vec{x}_{k+1}^{T}\textbf{Q}\vec{x}_{k+1} \ d\sigma + \rho^{2}\vec{u}^{T}\textbf{H}\vec{u},

where :math:`\vec{x}_{k+1}=\vec{x}_{k} + \vec{u}` is the predicted state optical state, :math:`\textbf{Q}` is the image quality matrix, :math:`\textbf{H}` is the control authority matrix, and :math:`\rho` is the penalty.
Based on the Gaussian quadrature rule, the cost function can be rewritten to be:

.. math::

    J(\vec{u}) = \sum_{i \in \mathbb{O}}w_{i} ( \vec{x}^{T}_{k+1}\textbf{Q}\vec{x}_{k+1})_{i} + \rho^{2}\vec{u}^{T}\textbf{H}\vec{u},

where :math:`w_{i}` is the weighting ratio for the optical filed point :math:`i`.

Differentiate :math:`J(\vec{u})` with respect to :math:`\vec{u}` and set the value as 0(`Cost Function Minimization <https://confluence.lsstcorp.org/display/LTS/Cost+Function+Minimization>`_), we have:

.. math::

    \begin{align*}
    \vec{u} &= -\frac{\sum_{i}w_{i}(\textbf{Q}\vec{x}_{k})_{i}} {\sum_{i}w_{i}\textbf{Q}_{i} + \rho^{2}\textbf{H}} \\ &= - \textbf{F}\sum_{i}w_{i}(\textbf{Q}\vec{x}_{k})_{i},
    \end{align*}

where the matrix :math:`\textbf{F}` is:

.. math::

    \textbf{F} = \text{inv}\left(\sum_{i}w_{i}\textbf{Q}_{i} + \rho^{2}\textbf{H}\right).

For the control authority matrix :math:`\textbf{H}`, it is defined to be:

.. math::

    \textbf{H} \equiv \text{diag}(\vec{\rho}_{h}\vec{h}^{T})^{2},

where :math:`\vec{h}` is the authority of subsystem and :math:`\vec{\rho}_{h}` is the penalty of :math:`\vec{h}`.
The change of 1 um (e.g. hexapod position) is assumed to be the same as 1 N*RMS (e.g. mirror bending mode).

For the image quality matrix :math:`\textbf{Q}`, we choose:

.. math::

    \vec{x}^{T}\textbf{Q}\vec{x} = \vec{p}^{T}\vec{p},

where :math:`\vec{p}` is the image quality vector.
It relates to the wavefront error :math:`\vec{y}` as the following:

.. math::

    \vec{p} = \textbf{C}(\vec{y} - \vec{y}_{2} - \vec{y}_{c}(l)).

And we have:

.. math::

    \begin{align*}
    \vec{x}^{T}\textbf{Q}\vec{x} &= (\textbf{C}(\vec{y} - \vec{y}_{2} - \vec{y}_{c}(l)))^{T}\textbf{C}(\vec{y} - \vec{y}_{2} - \vec{y}_{c}(l)) \\ 
    &= (\vec{y} - \vec{y}_{2} - \vec{y}_{c}(l))^{T}\textbf{C}^{T}\textbf{C}(\vec{y} - \vec{y}_{2} - \vec{y}_{c}(l)) \\
    &= (\textbf{A}\vec{x})^{T}\textbf{C}^{T}\textbf{C}\textbf{A}\vec{x} \\
    &= \vec{x}^{T}\textbf{A}^{T}\textbf{C}^{T}\textbf{C}\textbf{A}\vec{x}.
    \end{align*}

This means :math:`\textbf{Q} = \textbf{A}^{T}\textbf{C}^{T}\textbf{C}\textbf{A}`.
The matrix :math:`\textbf{C}^{T}\textbf{C}` is chosen to be:

.. math::
    \textbf{C}^{T}\text{C} \equiv \text{diag}(\vec\alpha),

where :math:`\vec{\alpha}` is the alpha value of normalized point source sensitivity (PSSN) in the basis :math:`\mathbb{Z}`.
The values are computed by fitting :math:`1 - PSSN = \alpha_k \delta_k^2`, where :math:`\delta_k` is the Zernike coefficient perturbation in microns. 
The units of :math:`\alpha_k` are in :math:`\mu m^{-2}`.

We can rewrite the matrix :math:`\textbf{F}` as:

.. math::

    \begin{align*}
    \textbf{F} &= \text{inv}\left(\sum_{i}w_{i}\textbf{Q}_{i} + \rho^{2}\textbf{H}\right) \\
    &= \text{inv}\left( \left( \frac{2\pi}{\lambda(\ell)} \right)^{2} \sum_{i}w_{i} (\textbf{A}^{T}\text{diag}(\vec\alpha)^{2}\textbf{A})_{i} + \rho^{2}\text{diag}(\vec{\rho}_{h}\vec{h}^{T})^{2}\right) \\
    &= \text{inv}\left (\left( \frac{2\pi}{\lambda(\ell)} \right)^{2} \sum_{i}w_{i}\textbf{M}_{i}^{T}\text{diag}(\vec\alpha)_{i}^{2}\textbf{M}_{i} + \rho^{2}\text{diag}(\vec{\rho}_{h}\vec{h}^{T})^{2}\right).
    \end{align*}

The offset :math:`\vec{u}` is:

.. math::

    \begin{align*}
    \vec{u} &= - \textbf{F}\sum_{i}w_{i}(\textbf{Q}\vec{x}_{k})_{i} \\
    &= - \left( \frac{2\pi}{\lambda(\ell)} \right)^{2} \textbf{F} \sum_{i}w_{i} \textbf{M}_{i}^{T}\text{diag}(\vec\alpha)_{i}^{2}\textbf{M}_{i} \vec{x}_{k, i}.
    \end{align*}

Consider the correction of wavefront error between center and corcer, we rewrite the above equation as:

.. math::

    \begin{align*}
    \vec{u} &= - \left( \frac{2\pi}{\lambda(\ell)} \right)^{2} \textbf{F} \sum_{i}w_{i} \textbf{M}_{i}^{T}\text{diag}(\vec\alpha)_{i}^{2} (\textbf{M}_{i} \vec{x}_{k, i} +\vec{y}_{2, i}) \\
    &= - \left( \frac{2\pi}{\lambda(\ell)} \right)^{2} \textbf{F} \sum_{i}w_{i} \textbf{M}_{i}^{T}\text{diag}(\vec\alpha)_{i}^{2} \vec{m}_{x, i}.
    \end{align*}

Consider three different reference points "x0, "0", and "x00". 

x0
    means the offset will only trace the previous one; 
0
    means the offset will trace the real value and target for 0;
x00
    means the offset will only trace the relative changes of offset without regarding the real value.

    Assume the telescope's state is :math:`\vec{s}_{0}` in the time :math:`k=0` and :math:`\vec{s}` in time :math:`k`, and we can intentionally shift :math:`\vec{m}_{x}` to be:

.. math::

    \begin{align*}
    \vec{m}_{x} &\rightarrow \vec{m}_{x}, \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \text{for x0} \\
    &\rightarrow \vec{m}_{x} + \rho^{2}\textbf{H}\vec{s}, \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \text{for 0} \\
    &\rightarrow \vec{m}_{x} + \rho^{2}\textbf{H}(\vec{s} - \vec{s}_{0}), \ \ \ \ \ \text{for x00}.
    \end{align*}

For the feedback control, instead of sending the full correction, it is usually to sent a ratio of offset.
So the final correction will be :math:`g\vec{u}` instead of :math:`\vec{u}`.