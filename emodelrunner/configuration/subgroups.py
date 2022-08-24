"""Dataclasses containing subgroups of config data."""

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


from dataclasses import dataclass
from typing import Optional

@dataclass
class HocPaths():
    """Contains paths relative to hoc files creation."""
    hoc_dir: str
    cell_hoc_filename: str
    simul_hoc_filename: str
    run_hoc_filename: str
    syn_dir: str
    syn_dir_for_hoc: str
    syn_hoc_filename: str
    main_protocol_filename: str


@dataclass
class ProtArgs():
    """Contains data needed to create protocols."""
    emodel: str
    apical_point_isec: int
    mtype: str
    prot_path: str
    features_path: str


@dataclass
class SynMechArgs():
    """Contains data needed to create synapse mechanimsms."""
    seed: int
    rng_settings_mode: str
    syn_conf_file: str
    syn_data_file: str
    syn_dir: str


@dataclass
class MorphArgs():
    """Contains data relative to morphology."""
    morph_path: str
    do_replace_axon: bool
    axon_hoc_path: Optional[str] = None


@dataclass
class PresynStimArgs():
    """Contains data relative to the presynaptic cell stimuli."""
    stim_train: float
    amp: float
    width: float
