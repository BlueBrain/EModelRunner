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

from bluepyopt import ephys

from emodelrunner.create_cells import create_cell_using_config
from emodelrunner.load import load_config
from emodelrunner.locations import SOMA_LOC
from emodelrunner.protocols import sscx_protocols
from emodelrunner.protocols.reader import ProtocolParser
from emodelrunner.protocols.reader import read_ramp_threshold_protocol
from emodelrunner.recordings import RecordingCustom
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

recordings = [
    RecordingCustom(
        name=".RampThresh.soma.v",
        location=SOMA_LOC,
        variable="v",
    )
]


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


def test_read_ramp_threshold_protocol():
    """Test read_ramp_threshold_protocol."""
    protocol_definition = {
        "type": "RampThresholdProtocol",
        "stimuli": {
            "ramp": {
                "ramp_delay": 70.0,
                "thresh_perc_start": 150.0,
                "thresh_perc_end": 250.0,
                "ramp_duration": 200.0,
                "totduration": 300.0
            },
            "holding": {
                "totduration": 300.0
            }
        }
    }
    prot = read_ramp_threshold_protocol("RampThresh", protocol_definition, recordings)
    assert isinstance(prot, sscx_protocols.RampThresholdProtocol)
    assert prot.name == "RampThresh"
    assert len(prot.stimuli) == 2
    assert isinstance(prot.stimuli[0], ephys.stimuli.NrnRampPulse)
    assert isinstance(prot.stimuli[1], ephys.stimuli.NrnSquarePulse)
    assert prot.ramp_stimulus == prot.stimuli[0]
    assert prot.holding_stimulus == prot.stimuli[1]
    assert prot.ramp_stimulus.location == SOMA_LOC
    assert prot.holding_stimulus.location == SOMA_LOC
    assert prot.ramp_stimulus.total_duration == 300.0
    assert prot.holding_stimulus.total_duration == 300.0
    assert prot.step_delay == 70.0
    assert prot.step_duration == 200.0
    assert prot.thresh_perc_start == 150.0
    assert prot.thresh_perc_end == 250.0
    assert prot.recordings == recordings
