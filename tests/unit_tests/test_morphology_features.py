"""Unit tests for morphology features."""

import os
import neurom as nm
from neurom.core.types import NeuriteType
from emodelrunner.factsheets import morphology_features


test_morph_dir = "examples/sscx_sample_dir/morphology"
test_morph = os.path.join(
    test_morph_dir, "dend-C270999B-P3_axon-C060110A3_-_Scale_x1.000_y0.950_z1.000.asc"
)


def test_morphology_factsheet_builder():
    """Test morphology factsheet builder class."""
    factsheet_builder = morphology_features.MorphologyFactsheetBuilder(test_morph)

    morph_features = factsheet_builder.get_all_feature_values()
    assert len(morph_features) == 13

    for feature in morph_features:
        assert feature["value"] >= 0


def test_total_length():
    """Test total length morphology feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalLength(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert abs(feature_dict["value"] - 11316.388908624649) <= 1e-3
    assert feature_dict["unit"] == "\u00b5m"


def test_neurite_volumes():
    """Test neurite volumes feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.NeuriteVolumes(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert abs(feature_dict["value"] - 2298.9971235076514) <= 1e-3
    assert feature_dict["unit"] == "\u00b5m\u00b3"


def test_max_branch_order():
    """Test max branch order feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.MaxBranchOrder(
        morphology, "apical_dendrite", NeuriteType.apical_dendrite
    )
    feature_dict = feature.to_dict()
    assert feature_dict["value"] == 12
    assert feature_dict["unit"] == ""


def test_max_section_length():
    """Test max section length feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.MaxSectionLength(
        morphology, "basal_dendrite", NeuriteType.basal_dendrite
    )
    feature_dict = feature.to_dict()
    assert abs(feature_dict["value"] - 314.51974) <= 1e-5
    assert feature_dict["unit"] == "\u00b5m"


def test_soma_diameter():
    """Test the some diameter feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.SomaDiamater(morphology)
    feature_dict = feature.to_dict()
    assert abs(feature_dict["value"] - 19.873456954956055) <= 1e-5
    assert feature_dict["unit"] == "\u00b5m"
