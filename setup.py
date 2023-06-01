#!/usr/bin/env python
"""EModelRunner setup."""

# Copyright 2020-2022 Blue Brain Project / EPFL

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 7):
    sys.exit("Sorry, Python < 3.7 is not supported")

# read the contents of the README file
with open("README.rst", encoding="utf-8") as f:
    README = f.read()

setup(
    name="EModelRunner",
    author="Blue Brain Project, EPFL",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="Runs cells from Blue Brain Project cell packages, such as sscx, synapse plasticity, etc.",
    long_description=README,
    long_description_content_type="text/x-rst",
    url="https://github.com/BlueBrain/EModelRunner",
    project_urls={
        "Tracker": "https://github.com/BlueBrain/EModelRunner/issues",
        "Source": "https://github.com/BlueBrain/EModelRunner",
        "Documentation": "https://emodelrunner.readthedocs.io/en/latest",
    },
    license="Apache 2.0",
    install_requires=[
        "numpy",
        "efel>=4.2,<5",
        "bluepyopt>=1.13.168",
        "neurom>=3.1.0",
        "h5py",
        "matplotlib",
        "schema",
        "Pebble>=4.3.10",
        "importlib_metadata; python_version<'3.8'",
        "tqdm>=4.65.0",
    ],
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.7",
    extras_require={"docs": ["sphinx", "sphinx-bluebrain-theme"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    include_package_data=True,
)
