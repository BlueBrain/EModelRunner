"""Unit tests for locations.py."""

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

from emodelrunner.locations import multi_locations


def test_multi_locations():
    """Test multi_locations function."""
    locs = multi_locations("alldend")
    assert len(locs) == 2
    assert {"basal", "apical"} == {loc.name for loc in locs}
    assert {"basal", "apical"} == {loc.seclist_name for loc in locs}

    locs = multi_locations("somadend")
    assert len(locs) == 3
    assert {"basal", "apical", "somatic"} == {loc.name for loc in locs}
    assert {"basal", "apical", "somatic"} == {loc.seclist_name for loc in locs}

    locs = multi_locations("somaxon")
    assert len(locs) == 2
    assert {"axonal", "somatic"} == {loc.name for loc in locs}
    assert {"axonal", "somatic"} == {loc.seclist_name for loc in locs}

    locs = multi_locations("allact")
    assert len(locs) == 4
    assert {"axonal", "somatic", "basal", "apical"} == {loc.name for loc in locs}
    assert {"axonal", "somatic", "basal", "apical"} == {
        loc.seclist_name for loc in locs
    }

    locs = multi_locations("custom")
    assert len(locs) == 1
    assert locs[0].name == "custom"
    assert locs[0].seclist_name == "custom"
