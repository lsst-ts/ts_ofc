# Optical Feedback Control (OFC) in Python

*This module is used to calculate the aggregated degree of freedom (DOF) for the hexpods and mirrors. The process contains: (1) estimate the optical state in the basis of DOF, (2) estimate the offset of DOF used in the next iteration/ visit, and (3) rotate the DOF based on the camera rotation angle.*

## 1. Version History

The version history is [here](./doc/VersionHistory.md).

*Author: Te-Wei Tsai*

## 2. Platform

- *CentOS 7*
- *Python: 3.6.6*
- *Scientific pipeline (newinstall.sh from master branch)*

## 3. Needed Package

- *ts_tcs_wep - develop branch (commit: d59002a)*

## 4. Use of Module

*1. Setup the WEP environment:* \
`export PYTHONPATH=$PYTHONPATH:$path_to_ts_tcs_wep/python` \
(e.g. `export PYTHONPATH=$PYTHONPATH:/home/ttsai/Document/stash/ts_tcs_wep/python`)

*2. Setup the OFC environment by eups:*

```bash
cd $ts_ofc_directory
setup -k -r .
scons
```

## 5. Content

*The strategy pattern is used for the algorithm study. The decorator pattern is used for the data/ parameters needed in the new algorithm if necessary. The details of cotent is [here](./doc/Content.md).*

## 6. Extension of Algorithm

- **Estimate the optical state**: Inherit from the OptStateEstiDefault class, and realize the estiOptState() function. Inherit from the Decorator class if new parameter data is needed in the new algorithm.
- **Calculate the DOF offset**: Inherit from the OptCtrlDefault class, and realize the estiUkWithoutGain() function. Inherit from the Decorator class if new parameter data is needed in the new algorithm.

## 7. Reference of Baseline Algorithm

1. Angeli, George Z. et al., Real time wavefront control system for the Large Synoptic Survey Telescope (LSST), Proc. SPIE 9150, Modeling, Systems Engineering, and Project Management for Astronomy VI, 91500H (2014). <https://doi.org/10.1117/12.2055390>
2. Angeli, George Z. et al., An integrated modeling framework for the Large Synoptic Survey Telescope (LSST), Proc. SPIE 9911, Modeling, Systems Engineering, and Project Management for Astronomy VI, 991118 (2016). <https://doi.org/10.1117/12.2234078>
3. Angeli, George Z. and Xin, Bo, Normalized Point Source Sensitivity for LSST, document-17242 (2016). <https://docushare.lsst.org/docushare/dsweb/Get/Document-17242>
4. [Details of optical state estimation and control algorithms.](https://confluence.lsstcorp.org/display/LTS/Control+Algorithm+in+Optical+Feedback+Control)
5. [Subsystem coordinate transformation.](https://confluence.lsstcorp.org/display/LTS/Subsystem+Coordinate+Transformation)
6. [Camera rotation and degree of freedom.](https://confluence.lsstcorp.org/display/LTS/Camera+Rotation+and+Degree+of+Freedom)
