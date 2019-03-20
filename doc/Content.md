# Content

*This module contains the following classes and functions ([class diagram](./ofcClassDiag.png)):*

- **ParamReaderYaml**: Parameter reader class to read the yaml configuration files used in the calculation.
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
- **BendModeToForce**: Bending mode to force class to transform the bending mode to actuator forces and vice versa.
- **SubSysAdap**: Subsystem adaptor class to transform the degree of freedom or actuator forces from ZEMAX coordinate to subsystem's coordinate and vice versa.

*There is one module in OFC:*

- **Control Interface (ctrlIntf)**: This module provides the interface classes to the main telescope active optics system (MTAOS). The factory pattern is applied to support the multiple instruments ([class diagram](./ctrlIntfClassDiag.png)).
  - **OFCCalculationFactory**: OFC calculation factory class to create the concrete OFC calculation object for each instrument.
  - **OFCCalculation**: OFC calculation default class as the parent class of concrete child classes for different instrument. The user shall get the concrete object by the creation method of OFCCalculationFactory class.
  - **OFCCalculationOfLsst**: OFC calculation of LSST class. This is the concrete child class of OFCCalculation class.
  - **OFCCalculationOfComCam**: OFC calculation of ComCam class. This is the concrete child class of OFCCalculation class.
  - **SensorWavefrontError**: Sensor wavefront error class. This class contains the information of sensor Id and related wavefront error. The details will be populated by the MTAOS and pass to the child class of OFCCalculation to do the calculation.
  - **CameraHexapodCorrection**: Camera hexapod correction class. This class contains the position correction to let the MTAOS to apply to subsystem.
  - **M2HexapodCorrection**: M2 hexapod correction class. This class contains the position correction to let the MTAOS to apply to subsystem.
  - **M1M3Correction**: M1M3 correction class. This class contains the actuator force correction to let the MTAOS to apply to subsystem.
  - **M2Correction**: M2 correction class. This class contains the actuator force correction to let the MTAOS to apply to subsystem.
  - **FWHMToPSSN**: Full width at half maximum (FWHM) to normalized point source sensitivity (PSSN) class. This class will convert the FWHM value to the PSSN. The details of this class is not clear yet. FWHM value will be provided by the data management (DM) team.
  - **FWHMSensorData**: Full width at half maximum (FWHM) sensor data class. This class has the information of sensor ID and related FWHM value. The details will be populated by the MTAOS and pass to the child class of OFCCalculation to do the calculation.
