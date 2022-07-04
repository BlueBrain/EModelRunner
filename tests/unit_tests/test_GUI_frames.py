"""Unit tests for the functions of the GUI frames module."""

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


from emodelrunner.GUI_utils.frames import positive_int_callback, float_callback


def test_positive_int_callback():
    """Test positive_int_callback function."""
    assert positive_int_callback("")
    assert positive_int_callback("54")
    assert not positive_int_callback("-10")
    assert not positive_int_callback("3.14")
    assert not positive_int_callback("not an int")


def test_float_callback():
    """Test float_callback function."""
    assert float_callback("")
    assert float_callback("54")
    assert float_callback("-10")
    assert float_callback("3.14")
    assert not float_callback("not an int")
