""""Unit tests for parsing utilities module."""

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

import logging
from unittest.mock import patch
import sys

from emodelrunner.parsing_utilities import get_parser_args, set_verbosity


def test_get_parser_args():
    """Test get_parser_args function."""
    # default verbosity case, also test config path argument
    sys.argv = "run.py --config_path mock/config/path".split()
    args = get_parser_args()

    assert args.config_path == "mock/config/path"
    assert args.verbosity == 0

    # --verbose case
    sys.argv = "run.py --config_path mock/config/path --verbose".split()
    args = get_parser_args()

    assert args.verbosity == 1

    # -v case
    sys.argv = "run.py --config_path mock/config/path -v".split()
    args = get_parser_args()

    assert args.verbosity == 1

    # -vv case
    sys.argv = "run.py --config_path mock/config/path -vv".split()
    args = get_parser_args()

    assert args.verbosity == 2


@patch("logging.basicConfig")
def test_set_verbosity(patch_basicConfig):
    """Test setting verbosity."""
    with patch("logging.StreamHandler", return_value="mock_val") as stream_handler:
        set_verbosity(-1)
        patch_basicConfig.assert_called_with(
            level=logging.WARNING, handlers=["mock_val"]
        )
        set_verbosity(1)
        patch_basicConfig.assert_called_with(level=logging.INFO, handlers=["mock_val"])
        set_verbosity(3)
        patch_basicConfig.assert_called_with(level=logging.DEBUG, handlers=["mock_val"])
        assert stream_handler.call_count == 3
