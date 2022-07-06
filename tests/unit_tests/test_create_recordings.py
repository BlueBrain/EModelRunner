"""Unit tests for create_recordings.py."""

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

from bluepyopt import ephys

from emodelrunner.create_recordings import get_pairsim_recordings
from emodelrunner.synapses.mechanism import NrnMODPointProcessMechanismCustom


def test_get_pairsim_recordings():
    """Test get_pairsim_recordings function."""
    presyn_prot_name = "presyn"
    postsyn_prot_name = "postsyn"
    # dummy point process mech
    mech = NrnMODPointProcessMechanismCustom(
        "syn_mechs",
        [],
        {},
        0,
        "Compatibility",
        None,
        None,
        use_glu_synapse=True,
        syn_setup_params=None,
    )
    syn_locs = [ephys.locations.NrnPointProcessLocation("synapse_locs", mech)]
    synrecs = ["cai_CR", "vsyn"]
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma", seclist_name="somatic", sec_index=0, comp_x=0.5
    )
    (pre_rec, post_rec) = get_pairsim_recordings(
        soma_loc, syn_locs, synrecs, presyn_prot_name, postsyn_prot_name
    )
    assert len(pre_rec) == 1
    assert pre_rec[0].name == "presyn"
    assert pre_rec[0].variable == "v"
    assert pre_rec[0].location.name == "soma"

    dict_recs = [
        {"name": rec.name, "v": rec.variable, "loc": rec.location.name}
        for rec in post_rec
    ]
    assert len(post_rec) == 3
    assert {"name": "postsyn", "v": "v", "loc": "soma"} in dict_recs
    assert {"name": "cai_CR", "v": "cai_CR", "loc": "synapse_locs"} in dict_recs
    assert {"name": "vsyn", "v": "vsyn", "loc": "synapse_locs"} in dict_recs
