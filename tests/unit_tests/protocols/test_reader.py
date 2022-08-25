"""Unit tests for the protocols.reader module."""

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

from pathlib import Path

from emodelrunner.create_cells import create_cell_using_config
from emodelrunner.load import (
    load_config,
)
from emodelrunner.protocols.reader import ProtocolParser
from emodelrunner.synapses.create_locations import get_syn_locs

from tests.utils import cwd

sscx_sample_dir = Path("examples") / "sscx_sample_dir"
thalamus_sample_dir = Path("examples") / "thalamus_sample_dir"

# fmt: off
sscx_recipe_protocol_keys = {
    "bAP", "APWaveform_360", "RMP", "SpikeRec_all", "ThresholdDetection", "Step_200",
    "Step_140", "Rin", "IV_-100", "Main", "RinHoldcurrent", "Step_280"}

thalamus_recipe_protocol_keys = {
    "ThresholdDetection_hyp", "Rin_dep", "ThresholdDetection_dep", "Rin_hyp", "Main",
    "RinHoldcurrent_hyp", "RMP", "Step_150", "Step_200", "Step_200_hyp", "RinHoldcurrent_dep"}
# fmt: on


class TestProtocolParser:
    """Tests for the ProtocolParser class."""

    def test_sscx_protocols_parser(self):
        """Test to assure all sscx protocols are parsed."""
        with cwd(sscx_sample_dir):
            config = load_config(
                config_path=Path("config") / "config_recipe_protocols.ini"
            )
            cell = create_cell_using_config(config)
            syn_locs = get_syn_locs(cell)
            prot_args = config.prot_args()

            protocols_dict = ProtocolParser().parse_sscx_protocols(
                protocols_filepath=prot_args.prot_path,
                prefix=prot_args.mtype,
                apical_point_isec=prot_args.apical_point_isec,
                syn_locs=syn_locs,
            )

            assert set(protocols_dict.keys()) == sscx_recipe_protocol_keys
            assert all(x is not None for x in protocols_dict)

    def test_thalamus_protocols_parser(self):
        """Test to assure all thalamus protocols are parsed."""
        with cwd(thalamus_sample_dir):
            config = load_config(
                config_path=Path("config") / "config_recipe_prots_short.ini"
            )
            prot_args = config.prot_args()

            protocols_dict = ProtocolParser().parse_thalamus_protocols(
                protocols_filepath=prot_args.prot_path,
                prefix=prot_args.mtype,
            )

            assert set(protocols_dict.keys()) == thalamus_recipe_protocol_keys
            assert all(x is not None for x in protocols_dict)
