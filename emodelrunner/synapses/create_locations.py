"""Functions to create synapse locations."""

# Copyright 2020-2021 Blue Brain Project / EPFL

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from bluepyopt import ephys


def get_syn_locs(cell):
    """Load synapse point process location.

    Args:
        cell (bluepyopt.ephys.models.CellModel): cell model containing the synapses

    Returns:
        list containing the synapse locations
    """
    syn_locs = []
    for mech in cell.mechanisms:
        if hasattr(mech, "pprocesses"):
            syn_locs.append(
                ephys.locations.NrnPointProcessLocation("synapse_locs", mech)
            )

    if not syn_locs:
        syn_locs = None

    return syn_locs
