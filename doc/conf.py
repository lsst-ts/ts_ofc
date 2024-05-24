"""Sphinx configuration file for an LSST stack package.

This configuration only affects single-package Sphinx documentation builds.
"""

from documenteer.conf.pipelinespkg import *  # noqa

project = "ts_ofc"
html_theme_options["logotext"] = project  # noqa
html_title = project
html_short_title = project
doxylink = {}


# Support the sphinx extension of mermaid
extensions = [
    "sphinxcontrib.mermaid",
    "sphinx_automodapi.automodapi",
]
