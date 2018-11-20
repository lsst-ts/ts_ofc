# Optical Feedback Control (OFC) in Python

*This module is used to calculate the aggregated degree of freedom (DOF) for the hexpods and mirrors. The process contains: (1) estimate the optical state in the basis of DOF, (2) estimate the offset of DOF used in the next iteration/ visit, and (3) rotate the DOF based on the camera rotation angle.*
<br/>
<br/>
*This repository is to fulfill the requirement that the scientist wants to change the OFC algorithm in Python script. This module will provide the interface python script to OFC with component template in LabVIEW in a latter time.*

## 1. Version History

*Version 1.0*
<br/>
*Finish the OFC with the support of algorithm study in Python.*

*Author: Te-Wei Tsai*
<br/>
*Date: 11-19-2018*

## 2. Platform

- *CentOS 7*
- *python: 3.6.2*

## 3. Needed Package

- *numpy*
- *scipy*
- *pytest (optional, test only.)*

## 4. Use of Module

*Setup the OFC environment:*
<br/>
`export PYTHONPATH=$PYTHONPATH:$path_to_ts_tcs_ofcPython_python`
<br/>
(e.g. `export PYTHONPATH=$PYTHONPATH:/home/ttsai/Documents/github/ts_tcs_ofcPython/python`)

## 5. Content

*The strategy pattern is used for the algorithm study. The decorator pattern is used for the data/ parameters needed in the new algorithm if necessary.*

*This module contains the following classes and functions ([class diagram](./doc/ofcPythonClassDiag.png)):*

- **DataShare**: Data share class for the information change used in the algorithms. This class includes the information of indexes of annular Zernike polynomials (zk) and DOF to use.
- **Decorator**: Decorator interface class to add the new functions or attributes to the DataShare class. This helps the user to get the parameters needed in the new algorithms. 
- **OptStateEstiDataDecorator**: Optical state estimator data decorator class. This adds the functions/ attributes to DataShare class for the parameters needed in the OptStateEsti class (baseline algorithm).
- **OptCtrlDataDecorator**: Optimal control data decorator class. This adds the functions/ attributes to DataShare class for the parameters needed in the OptCtrl class (baseline algorithm).
- **OptStateEstiDefault**: Optical state estimator default class. The abstract function interface is declared in this class. The child class should realize the abstract funtion to estimate the optical state in the basis of DOF.
- **OptStateEsti**: Optical state estimator class in the baseline algorithm. The optical state is estimated by the pseudo-inverse method.
- **OptCtrlDefault**: Optimal control default class. The abstract function interface is declared in this class. The child class should realize the abstract funtion to calculate the offset of DOF.
- **OptCtrl**: Optimal control class in the baseline algorithm. The offset is calculated by minimizing the cost function.
- **ZTAAC**: Zernike to actuator adjustment calculator class. The high-level class to integrate the DataShare, OptStateEstiDefault, and OptCtrlDefault classes.
- **CamRot**: Camera rotation class to rotate the calculated DOF offset.
- **Utility**: Some functions used in this module.
- **IterDataReader**: Iteration data reader class used in the unit test only. This is just to read the test iteration data.

## 6. Extension of Algorithm

- **Estimate the optical state**: Inherit from the OptStateEstiDefault class, and realize the estiOptState function. Inherit from the Decorator class if new parameter data is needed in the new algorithm.
- **Calculate the DOF offset**: Inherit from the OptCtrlDefault class, and realize the estiUkWithoutGain function. Inherit from the Decorator class if new parameter data is needed in the new algorithm.

## 7. Reference of Baseline Algorithm

1. Angeli, George Z. et al., Real time wavefront control system for the Large Synoptic Survey Telescope (LSST), Proc. SPIE 9150, Modeling, Systems Engineering, and Project Management for Astronomy VI, 91500H (2014). [https://doi.org/10.1117/12.2055390]
2. Angeli, George Z. et al., An integrated modeling framework for the Large Synoptic Survey Telescope (LSST), Proc. SPIE 9911, Modeling, Systems Engineering, and Project Management for Astronomy VI, 991118 (2016). [https://doi.org/10.1117/12.2234078]
3. Angeli, George Z. and Xin, Bo, Normalized Point Source Sensitivity for LSST, document-17242 (2016). [https://docushare.lsst.org/docushare/dsweb/Get/Document-17242]
4. [Details of optical state estimation and control algorithms.](https://confluence.lsstcorp.org/display/LTS/Control+Algorithm+in+Optical+Feedback+Control)
5. [Camera rotation and DOF.](https://confluence.lsstcorp.org/display/LTS/Camera+Rotation+and+Degree+of+Freedom)
