"""Unit tests for the create_protocols module."""

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
from types import SimpleNamespace

import pytest

from emodelrunner.load import (
    load_config,
)
from emodelrunner.create_cells import create_cell_using_config
from emodelrunner.protocols.create_protocols import ProtocolBuilder

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


class TestProtocolBuilder:
    """Test ProtocolBuilder class."""

    def test_using_sscx_protocols(self):
        """Test building sscx protocols object."""
        with cwd(sscx_sample_dir):
            config = load_config(
                config_path=Path("config") / "config_recipe_protocols.ini"
            )
            cell = create_cell_using_config(config)
            add_synapses = config.getboolean("Synapses", "add_synapses")
            prot_args = config.prot_args()

            protocols = ProtocolBuilder.using_sscx_protocols(
                add_synapses, prot_args, cell
            )
            ephys_protocols = protocols.get_ephys_protocols()

            prot_obj_names = {
                x.name for x in ephys_protocols.protocols[0].other_protocols
            }
            prot_obj_names.add(ephys_protocols.protocols[0].name)
            prot_obj_names.add(ephys_protocols.protocols[0].rmp_protocol.name)
            prot_obj_names.add(ephys_protocols.protocols[0].thdetect_protocol.name)
            prot_obj_names.add(ephys_protocols.protocols[0].rinhold_protocol.name)

            assert sscx_recipe_protocol_keys - prot_obj_names == {
                "Rin",
                "RinHoldcurrent",
                "ThresholdDetection",
            }
            assert prot_obj_names - sscx_recipe_protocol_keys == {
                "RinHoldCurrent",
                "IDRest",
            }

    def test_using_sscx_protocols_none_cell_exception(self):
        """Test building sscx protocols with a None cell to raise exception."""
        cell = None
        add_synapses = True

        with cwd(sscx_sample_dir):
            config = load_config(
                config_path=Path("config") / "config_recipe_protocols.ini"
            )
        prot_args = config.prot_args()

        with pytest.raises(RuntimeError):
            ProtocolBuilder.using_sscx_protocols(add_synapses, prot_args, cell)

    def test_using_thalamus_protocols(self):
        """Test building thalamus protocols object."""
        with cwd(thalamus_sample_dir):
            config = load_config(
                config_path=Path("config") / "config_recipe_prots_short.ini"
            )
            cell = create_cell_using_config(config)
            add_synapses = config.getboolean("Synapses", "add_synapses")
            prot_args = config.prot_args()

            protocols = ProtocolBuilder.using_thalamus_protocols(
                add_synapses, prot_args, cell
            )
            ephys_protocols = protocols.get_ephys_protocols()

            prot_obj_names = {
                x.name for x in ephys_protocols.protocols[0].other_protocols
            }
            prot_obj_names.add(ephys_protocols.protocols[0].name)
            prot_obj_names.add(ephys_protocols.protocols[0].rmp_protocol.name)
            prot_obj_names.add(ephys_protocols.protocols[0].thdetect_protocol_dep.name)
            prot_obj_names.add(ephys_protocols.protocols[0].thdetect_protocol_hyp.name)
            prot_obj_names.add(ephys_protocols.protocols[0].rinhold_protocol_dep.name)
            prot_obj_names.add(ephys_protocols.protocols[0].rinhold_protocol_hyp.name)

            assert thalamus_recipe_protocol_keys - prot_obj_names == {
                "Rin_hyp",
                "Rin_dep",
            }
            assert prot_obj_names - thalamus_recipe_protocol_keys == set()

    def test_thalamus_stim_currents_exception(self):
        """Tests the exception case in get_thalamus_stim_currents."""
        mtype = "test_mtype"
        responses = {
            f"{mtype}.bpo_threshold_current_hyp": 0.1,
            f"{mtype}.bpo_holding_current_hyp": 0.3,
            f"{mtype}.bpo_threshold_current_dep": 0.4,
        }

        mock_obj = SimpleNamespace(
            protocols=[SimpleNamespace(generate_current=(lambda *args: {"args": args}))]
        )

        thal_protocols = ProtocolBuilder(protocols=mock_obj)
        currents = thal_protocols.get_thalamus_stim_currents(responses, mtype, dt=0.025)
        assert currents["args"] == (0.1, None, 0.3, None, 0.025)
