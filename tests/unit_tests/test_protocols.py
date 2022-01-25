"""Unit tests for the protocols module."""

from pathlib import Path

from emodelrunner.load import (
    load_config,
    get_prot_args,
)
from emodelrunner.create_cells import create_cell_using_config
from emodelrunner.protocols.create_protocols import ProtocolBuilder
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
            prot_args = get_prot_args(config)

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

    def test_using_thalamus_protocols(self):
        """Test building thalamus protocols object."""
        with cwd(thalamus_sample_dir):
            config = load_config(
                config_path=Path("config") / "config_recipe_prots_short.ini"
            )
            cell = create_cell_using_config(config)
            add_synapses = config.getboolean("Synapses", "add_synapses")
            prot_args = get_prot_args(config)

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
            prot_args = get_prot_args(config)

            protocols_dict = ProtocolParser().parse_sscx_protocols(
                protocols_filepath=prot_args["prot_path"],
                prefix=prot_args["mtype"],
                apical_point_isec=prot_args["apical_point_isec"],
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
            prot_args = get_prot_args(config)

            protocols_dict = ProtocolParser().parse_thalamus_protocols(
                protocols_filepath=prot_args["prot_path"],
                prefix=prot_args["mtype"],
            )

            assert set(protocols_dict.keys()) == thalamus_recipe_protocol_keys
            assert all(x is not None for x in protocols_dict)
