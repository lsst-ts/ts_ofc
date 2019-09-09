# Optical Feedback Control (OFC)

*This module is used to calculate the aggregated degree of freedom (DOF) for the hexpods and mirrors.*

## 1. Platform

- *CentOS 7*
- *python: 3.7.2*
- *scientific pipeline (newinstall.sh from master branch)*

## 2. Needed Package

- *[ts_wep](https://github.com/lsst-ts/ts_wep) - master branch (commit: a9d5627)*
- *[documenteer](https://github.com/lsst-sqre/documenteer) (optional)*
- *[plantuml](http://plantuml.com) (optional)*
- *[sphinxcontrib-plantuml](https://pypi.org/project/sphinxcontrib-plantuml/) (optional)*

## 3. Use of Module

*Setup the WEP environment first, and then, setup the OFC environment by eups:*

```bash
cd $ts_ofc_directory
setup -k -r .
scons
```

## 4. Extension of Algorithm

- **Estimate the optical state**: Inherit from the OptStateEstiDefault class, and realize the estiOptState() function. Inherit from the Decorator class if new parameter data is needed in the new algorithm.
- **Calculate the DOF offset**: Inherit from the OptCtrlDefault class, and realize the estiUkWithoutGain() function. Inherit from the Decorator class if new parameter data is needed in the new algorithm.

## 5. Example Script

- **calcDof.py**: Calculate DOF with 5 iterations.

## 6. Build the Document

*The user can use `package-docs build` to build the documentation. The packages of documenteer, plantuml, and sphinxcontrib-plantuml are needed. The path of plantuml.jar in doc/conf.py needs to be updated to the correct path. To clean the built documents, use `package-docs clean`. See [Building single-package documentation locally](https://developer.lsst.io/stack/building-single-package-docs.html) for further details.*

## 7. Reference of Baseline Algorithm

1. Angeli, George Z. et al., Real time wavefront control system for the Large Synoptic Survey Telescope (LSST), Proc. SPIE 9150, Modeling, Systems Engineering, and Project Management for Astronomy VI, 91500H (2014). <https://doi.org/10.1117/12.2055390>
2. Angeli, George Z. et al., An integrated modeling framework for the Large Synoptic Survey Telescope (LSST), Proc. SPIE 9911, Modeling, Systems Engineering, and Project Management for Astronomy VI, 991118 (2016). <https://doi.org/10.1117/12.2234078>
3. Angeli, George Z. and Xin, Bo, Normalized Point Source Sensitivity for LSST, document-17242 (2016). <https://docushare.lsst.org/docushare/dsweb/Get/Document-17242>
4. [Details of optical state estimation and control algorithms.](https://confluence.lsstcorp.org/display/LTS/Control+Algorithm+in+Optical+Feedback+Control)
5. [Subsystem coordinate transformation.](https://confluence.lsstcorp.org/display/LTS/Subsystem+Coordinate+Transformation)
6. [Camera rotation and degree of freedom.](https://confluence.lsstcorp.org/display/LTS/Camera+Rotation+and+Degree+of+Freedom)
