[![docs](https://img.shields.io/badge/docs-ts--ofc.lsst.io-brightgreen)](https://ts-ofc.lsst.io/)

# Optical Feedback Control (OFC)

This module is used to calculate the aggregated degree of freedom (DOF) for the hexapods and mirrors.

See the docs: https://ts-ofc.lsst.io/

## Supported OS + Packages

- CentOS 7
- python: >3.8

## Required LSST Packages

- [black](https://github.com/psf/black) (optional)
- [documenteer](https://github.com/lsst-sqre/documenteer) (optional)
- [plantuml](http://plantuml.com) (optional)
- [sphinxcontrib-plantuml](https://pypi.org/project/sphinxcontrib-plantuml/) (optional)

## Use of Module

Setup the WEP environment first, and then, setup the OFC environment by `eups`:

```bash
cd $ts_ofc_directory
setup -k -r .
scons
```

## Code Format

This code is automatically formatted by `black` using a git pre-commit hook.
To enable this:

1. Install the `black` Python package.
2. Run `git config core.hooksPath .githooks` once in this repository.

## Build the Document

To build project documentation, run `package-docs build` to build the documentation.
The packages of **documenteer**, **plantuml**, and **sphinxcontrib-plantuml** are needed.
The path of `plantuml.jar` in `doc/conf.py` needs to be updated to the correct path.
To clean the built documents, use `package-docs clean`.
See [Building single-package documentation locally](https://developer.lsst.io/stack/building-single-package-docs.html) for further details.
