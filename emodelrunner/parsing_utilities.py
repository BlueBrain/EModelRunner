"""Parsing utilities functions."""

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

import argparse
import logging


def get_parser_args():
    """Get config_path and verbosity from argparse.

    Returns:
        argparse.Namespace: object containing the parsed arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config_path",
        default=None,
        help="the path to the config file.",
    )
    parser.add_argument("-v", "--verbose", action="count", dest="verbosity", default=0)
    return parser.parse_args()


def set_verbosity(verbosity):
    """Set verbosity level.

    Args:
        verbosity (int): verbosity level. 0 for warning, 1 for info and 2 or more for debug
    """
    if verbosity > 2:
        verbosity = 2
    elif verbosity < 0:
        verbosity = 0

    logging.basicConfig(
        level=(logging.WARNING, logging.INFO, logging.DEBUG)[verbosity],
        handlers=[logging.StreamHandler()],
    )
