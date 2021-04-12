#!/usr/bin/env python

import imp
import sys

from setuptools import setup, find_packages

if sys.version_info < (2, 7):
    sys.exit("Sorry, Python < 2.7 is not supported")

# read the contents of the README file
if sys.version_info < (3, 0):
    import io

    with io.open("README.rst", encoding="utf-8") as f:
        README = f.read()
else:
    with open("README.rst", encoding="utf-8") as f:
        README = f.read()

VERSION = imp.load_source("", "emodelrunner/version.py").__version__

setup(
    name="EModelRunner",
    author="Aurelien Jaquier, Anil Tuncel",
    author_email="bbp-ou-cell@groupes.epfl.ch",
    version=VERSION,
    description="The name is telling what it does (it runs the emodels :))",
    long_description=README,
    long_description_content_type="text/x-rst",
    url="https://bbpteam.epfl.ch/documentation/projects/EModelRunner",
    project_urls={
        "Tracker": "https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
        "Source": "ssh://bbpcode.epfl.ch/cells/EModelRunner",
    },
    license="BBP-internal-confidential",
    install_requires=[
        "numpy",
        "bluepyopt",
        "neurom",
        "h5py",
    ],
    packages=find_packages(),
    python_requires=">=2.7",
    extras_require={"docs": ["sphinx", "sphinx-bluebrain-theme"]},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    include_package_data=True,
)
