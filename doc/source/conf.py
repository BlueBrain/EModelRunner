# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("."))

try:
    # available since py3.8+
    from importlib.metadata import version as get_version
except ModuleNotFoundError:
    from importlib_metadata import version as get_version

from pathlib import Path
import shutil

# -- copy images referenced in Readme ---------------------------------------

Path("doc/source/images").mkdir(parents=True, exist_ok=True)
shutil.copy("images/GUI_screenshot.png", "doc/source/images/GUI_screenshot.png")


# -- Project information -----------------------------------------------------

project = "EModelRunner"

release = get_version("emodelrunner")
version = release


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

# Add any paths that contain templates here, relative to this directory.
# templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    # references twice, in protocols.RatSSCxMainProtocol
    # once in Attributes, and once in a property method
    "exclude-members": "rin_efeature",
}
# so that we don't have to install neuron matplotlib, tkinter
# (imported in GUI) to do the docs
autodoc_mock_imports = ["neuron", "matplotlib", "tkinter"]
# to be able to put multiple return variables in the docstrings
# napoleon_custom_sections = [("Returns", "params_style")]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx-bluebrain-theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

html_theme_options = {
    "metadata_distribution": "emodelrunner",
}

html_title = "EModelRunner"

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False
