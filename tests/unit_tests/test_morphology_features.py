"""Unit tests for morphology features."""

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

    morph_features = factsheet_builder.get_sscx_feature_values()
    assert len(morph_features) == 13

    for feature in morph_features:
        print(feature)
        assert feature["value"] >= 0


def test_total_length():
    """Test total length morphology feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalLength(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon length"
    assert abs(feature_dict["value"] - 11316.388908624649) <= 1e-3
    assert feature_dict["unit"] == "\u00b5m"


def test_total_height():
    """Test total height feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalHeight(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon height"
    assert abs(feature_dict["value"] - 965.4704) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m"


def test_total_width():
    """Test total width feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalWidth(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon width"
    assert abs(feature_dict["value"] - 768.3234) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m"


def test_total_depth():
    """Test total depth feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalDepth(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon depth"
    assert abs(feature_dict["value"] - 887.29956) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m"


def test_total_area():
    """Test the total area feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalArea(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon area"
    assert abs(feature_dict["value"] - 14800.92929) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m\u00b2"


def test_total_volume():
    """Test the total volume feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalVolume(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon volume"
    assert abs(feature_dict["value"] - 2298.997123) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m\u00b3"


def test_number_of_sections():
    """Test number of sections feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.NumberOfSections(
        morphology, "basal_dendrite", NeuriteType.basal_dendrite
    )
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "number of basal_dendrite sections"
    assert feature_dict["value"] == 51
    assert feature_dict["unit"] == ""


def test_mean_neurite_volumes():
    """Test neurite volumes feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.MeanNeuriteVolumes(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "mean axon volume"
    assert abs(feature_dict["value"] - 2298.9971235076514) <= 1e-3
    assert feature_dict["unit"] == "\u00b5m\u00b3"


def test_max_branch_order():
    """Test max branch order feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.MaxBranchOrder(
        morphology, "apical_dendrite", NeuriteType.apical_dendrite
    )
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "apical_dendrite maximum branch order"
    assert feature_dict["value"] == 12
    assert feature_dict["unit"] == ""


def test_max_section_length():
    """Test max section length feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.MaxSectionLength(
        morphology, "basal_dendrite", NeuriteType.basal_dendrite
    )
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "basal_dendrite maximum section length"
    assert abs(feature_dict["value"] - 314.51974) <= 1e-5
    assert feature_dict["unit"] == "\u00b5m"


def test_soma_diameter():
    """Test the some diameter feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.SomaDiamater(morphology)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "soma diameter"
    assert abs(feature_dict["value"] - 19.873456954956055) <= 1e-5
    assert feature_dict["unit"] == "\u00b5m"


def test_soma_surface_area():
    """Test the soma surface area feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.SomaSurfaceArea(morphology)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "soma surface area"
    assert abs(feature_dict["value"] - 1240.78550) <= 1e-5
    assert feature_dict["unit"] == "\u00b5m\u00b2"


def test_soma_volume():
    """Test the soma volume feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.SomaVolume(morphology)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "soma volume"
    assert abs(feature_dict["value"] - 4109.782871) <= 1e-5
    assert feature_dict["unit"] == "\u00b5m\u00b3"
