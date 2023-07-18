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
from pytest import raises

from bluepyopt import ephys

from emodelrunner.create_cells import create_cell_using_config
from emodelrunner.load import load_config
from emodelrunner.locations import SOMA_LOC
from emodelrunner.protocols import sscx_protocols
from emodelrunner.protocols import thalamus_protocols
from emodelrunner.protocols.reader import ProtocolParser
from emodelrunner.protocols.reader import read_netstim_protocol
from emodelrunner.protocols.reader import read_ramp_protocol
from emodelrunner.protocols.reader import read_ramp_threshold_protocol
from emodelrunner.protocols.reader import read_step_protocol
from emodelrunner.protocols.reader import read_step_threshold_protocol
from emodelrunner.protocols.reader import read_vecstim_protocol
from emodelrunner.recordings import RecordingCustom
from emodelrunner.synapses.create_locations import get_syn_locs
from emodelrunner.synapses.stimuli import NrnNetStimStimulusCustom
from emodelrunner.synapses.stimuli import NrnVecStimStimulusCustom


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
                "totduration": 300.0,
            },
            "holding": {"totduration": 300.0},
        },
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


def test_read_ramp_protocol():
    """Test read_ramp_protocol."""
    protocol_definition = {
        "type": "RampProtocol",
        "stimuli": {
            "ramp": {
                "ramp_delay": 70.0,
                "ramp_amplitude_start": 150.0,
                "ramp_amplitude_end": 250.0,
                "ramp_duration": 200.0,
                "totduration": 300.0,
            },
            "holding": {
                "delay": 0.0,
                "amp": -0.0896244038173676,
                "duration": 300.0,
                "totduration": 300.0,
            },
        },
    }
    prot = read_ramp_protocol("Ramp", protocol_definition, recordings)
    assert isinstance(prot, sscx_protocols.RampProtocol)
    assert prot.name == "Ramp"
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
    assert prot.ramp_stimulus.ramp_amplitude_start == 150.0
    assert prot.ramp_stimulus.ramp_amplitude_end == 250.0
    assert prot.recordings == recordings
    assert prot.holding_stimulus.step_delay == 0.0
    assert prot.holding_stimulus.step_amplitude == -0.0896244038173676
    assert prot.holding_stimulus.step_duration == 300.0

    # no holding case
    protocol_definition["stimuli"].pop("holding")
    prot = read_ramp_protocol("Ramp", protocol_definition, recordings)
    assert len(prot.stimuli) == 1
    assert isinstance(prot.stimuli[0], ephys.stimuli.NrnRampPulse)
    assert prot.holding_stimulus is None


def test_read_step_protocol():
    """Test read_step_protocol."""
    protocol_definition = {
        "type": "StepProtocol",
        "stimuli": {
            "step": {
                "delay": 70.0,
                "amp": 0.34859375,
                "duration": 200.0,
                "totduration": 300.0,
            },
            "holding": {
                "delay": 0.0,
                "amp": -0.0896244038173676,
                "duration": 300.0,
                "totduration": 300.0,
            },
        },
    }

    # sscx protocol
    prot = read_step_protocol("Step", sscx_protocols, protocol_definition, recordings)
    assert isinstance(prot, sscx_protocols.StepProtocol)
    assert prot.name == "Step"
    assert len(prot.stimuli) == 2
    assert isinstance(prot.stimuli[0], ephys.stimuli.NrnSquarePulse)
    assert isinstance(prot.stimuli[1], ephys.stimuli.NrnSquarePulse)
    assert len(prot.step_stimuli) == 1
    assert prot.stimuli[0] == prot.step_stimuli[0]
    assert prot.stimuli[1] == prot.holding_stimulus
    assert prot.stochkv_det is None
    assert prot.step_stimuli[0].location == SOMA_LOC
    assert prot.holding_stimulus.location == SOMA_LOC
    assert prot.step_stimuli[0].total_duration == 300.0
    assert prot.holding_stimulus.total_duration == 300.0
    assert prot.stim_start == 70.0
    assert prot.stim_duration == 200.0
    assert prot.stim_end == 270.0
    assert prot.stim_last_start == 70.0
    assert prot.step_amplitude == 0.34859375
    assert prot.recordings == recordings
    assert prot.holding_stimulus.step_delay == 0.0
    assert prot.holding_stimulus.step_amplitude == -0.0896244038173676
    assert prot.holding_stimulus.step_duration == 300.0

    # thalamus protocol
    prot = read_step_protocol(
        "Step", thalamus_protocols, protocol_definition, recordings
    )
    assert isinstance(prot, thalamus_protocols.StepProtocolCustom)
    assert prot.name == "Step"
    assert len(prot.stimuli) == 2
    assert isinstance(prot.stimuli[0], ephys.stimuli.NrnSquarePulse)
    assert isinstance(prot.stimuli[1], ephys.stimuli.NrnSquarePulse)
    assert prot.stimuli[0] == prot.step_stimulus
    assert prot.stimuli[1] == prot.holding_stimulus
    assert prot.stochkv_det is None
    assert prot.stim_start == 70.0
    assert prot.stim_end == 270.0
    assert prot.step_amplitude == 0.34859375

    # no holding case
    # amp is None case
    protocol_definition["stimuli"]["step"]["amp"] = None
    protocol_definition["stimuli"].pop("holding")
    prot = read_step_protocol("Step", sscx_protocols, protocol_definition, recordings)
    assert prot.step_amplitude is None
    assert prot.holding_stimulus is None
    assert len(prot.stimuli) == 1

    # bad module case
    with raises(ValueError):
        prot = read_step_protocol(
            "Step", "non-existing module", protocol_definition, recordings
        )


def test_read_step_threshold_protocol():
    """Test read_step_threshold_protocol."""
    protocol_definition = {
        "type": "StepThresholdProtocol",
        "stimuli": {
            "step": {
                "delay": 70.0,
                "amp": None,
                "thresh_perc": 139.7246,
                "duration": 200.0,
                "totduration": 300.0,
            }
        },
    }

    # sscx protocol
    prot = read_step_threshold_protocol(
        "StepThresh", sscx_protocols, protocol_definition, recordings
    )
    assert isinstance(prot, sscx_protocols.StepThresholdProtocol)
    assert prot.name == "StepThresh"
    assert len(prot.stimuli) == 2
    assert isinstance(prot.stimuli[0], ephys.stimuli.NrnSquarePulse)
    assert isinstance(prot.stimuli[1], ephys.stimuli.NrnSquarePulse)
    assert len(prot.step_stimuli) == 1
    assert prot.stimuli[0] == prot.step_stimuli[0]
    assert prot.stimuli[1] == prot.holding_stimulus
    assert prot.stochkv_det is None
    assert prot.step_stimuli[0].location == SOMA_LOC
    assert prot.holding_stimulus.location == SOMA_LOC
    assert prot.step_stimuli[0].total_duration == 300.0
    assert prot.holding_stimulus.total_duration == 300.0
    assert prot.stim_start == 70.0
    assert prot.stim_duration == 200.0
    assert prot.stim_end == 270.0
    assert prot.stim_last_start == 70.0
    assert prot.step_amplitude is None
    assert prot.thresh_perc == 139.7246
    assert prot.recordings == recordings
    assert prot.holding_stimulus.step_delay == 0.0
    assert prot.holding_stimulus.step_duration == 300.0

    # thalamus protocol
    prot = read_step_threshold_protocol(
        "StepThresh", thalamus_protocols, protocol_definition, recordings
    )
    assert isinstance(prot, thalamus_protocols.StepThresholdProtocol)
    assert prot.name == "StepThresh"
    assert len(prot.stimuli) == 2
    assert isinstance(prot.stimuli[0], ephys.stimuli.NrnSquarePulse)
    assert isinstance(prot.stimuli[1], ephys.stimuli.NrnSquarePulse)
    assert prot.stimuli[0] == prot.step_stimulus
    assert prot.stimuli[1] == prot.holding_stimulus
    assert prot.stochkv_det is None
    assert prot.stim_start == 70.0
    assert prot.stim_end == 270.0
    assert prot.step_amplitude is None

    # bad module case
    with raises(ValueError):
        prot = read_step_threshold_protocol(
            "Step", "non-existing module", protocol_definition, recordings
        )


def test_read_vecstim_protocol():
    """Test read_vecstim_protocol."""
    protocol_definition = {
        "type": "Vecstim",
        "stimuli": {
            "syn_stop": 3000.0,
            "syn_start": 50.0,
            "syn_stim_seed": 42,
            "vecstim_random": "neuron",
        },
    }
    # use syn_locs = None for simplicity
    syn_locs = None

    prot = read_vecstim_protocol("Vecstim", protocol_definition, recordings, syn_locs)
    assert isinstance(prot, sscx_protocols.SweepProtocolCustom)
    assert prot.name == "Vecstim"
    assert prot.recordings == recordings
    assert isinstance(prot.stimuli[0], NrnVecStimStimulusCustom)
    assert prot.stimuli[0].locations is None
    assert prot.stimuli[0].start == 50.0
    assert prot.stimuli[0].total_duration == 3000.0
    assert prot.stimuli[0].seed == 42
    assert prot.stimuli[0].vecstim_random == "neuron"
    assert prot.stimuli[0].pre_spike_train is None

    # vecstim_random not python nor neuron case
    protocol_definition["stimuli"]["vecstim_random"] = "unknown"
    prot = read_vecstim_protocol("Vecstim", protocol_definition, recordings, syn_locs)
    assert prot.stimuli[0].vecstim_random == "python"

    # stop is None case
    protocol_definition["stimuli"]["syn_stop"] = None
    with raises(ValueError):
        prot = read_vecstim_protocol(
            "Vecstim", protocol_definition, recordings, syn_locs
        )


def test_read_netstim_protocol():
    """Test read_netstim_protocol."""
    protocol_definition = {
        "type": "Netstim",
        "stimuli": {
            "syn_start": 50.0,
            "syn_stop": 300.0,
            "syn_nmb_of_spikes": 10.0,
            "syn_interval": 10.0,
            "syn_noise": 0.0,
        },
    }
    # use syn_locs = None for simplicity
    syn_locs = None

    prot = read_netstim_protocol("Netstim", protocol_definition, recordings, syn_locs)
    assert isinstance(prot, sscx_protocols.SweepProtocolCustom)
    assert prot.name == "Netstim"
    assert prot.recordings == recordings
    assert isinstance(prot.stimuli[0], NrnNetStimStimulusCustom)
    assert prot.stimuli[0].locations is None
    assert prot.stimuli[0].interval == 10.0
    assert prot.stimuli[0].number == 10.0
    assert prot.stimuli[0].start == 50.0
    assert prot.stimuli[0].noise == 0.0
    assert prot.stimuli[0].total_duration == 300.0

    # stop is None case
    protocol_definition["stimuli"]["syn_stop"] = None
    with raises(ValueError):
        prot = read_netstim_protocol(
            "Netstim", protocol_definition, recordings, syn_locs
        )
