"""Sphinx configuration file for an LSST stack package.

This configuration only affects single-package Sphinx documentation builds.
"""

import os.path

from documenteer.conf.pipelinespkg import *  # noqa

project = "ts_ofc"
html_theme_options["logotext"] = project  # noqa
html_title = project
html_short_title = project
doxylink = {}


# Support the sphinx extension of plantuml
extensions.append("sphinxcontrib.plantuml")  # noqa

# Put the path to plantuml.jar
plantuml_path = os.path.expanduser("~/plantuml.jar")
plantuml = f"java -jar {plantuml_path}"
