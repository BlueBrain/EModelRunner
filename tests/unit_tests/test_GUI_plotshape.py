"""Unit tests for the functions of the GUI plotshape module."""

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

from matplotlib import cm

from emodelrunner.GUI_utils.plotshape import get_color_from_cmap


def test_get_color_from_cmap():
    """Test get_color_from_cmap function."""
    cmap = cm.binary
    assert get_color_from_cmap(0, 0, 0, cmap) == "black"
    assert get_color_from_cmap(0, 10, 0, cmap) == "black"
    assert get_color_from_cmap(-50, -70, 30, cmap) == (0.8, 0.8, 0.8, 1.0)
