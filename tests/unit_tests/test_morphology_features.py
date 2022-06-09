"""Unit tests for morphology features."""

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

import os
import json
import neurom as nm
from neurom.core.types import NeuriteType
from emodelrunner.factsheets import morphology_features


test_morph_dir = "examples/sscx_sample_dir/morphology"
test_morph = os.path.join(
    test_morph_dir,
    "dend-C231296A-P4B2_axon-C200897C-P2_-_Scale_x1.000_y0.975_z1.000.asc",
)


def test_sscx_morphology_factsheet_builder():
    """Test morphology factsheet builder class."""
    factsheet_builder = morphology_features.SSCXMorphologyFactsheetBuilder(test_morph)
    morph_features = factsheet_builder.get_feature_values()
    assert len(morph_features) == 13
    for feature in morph_features:
        assert feature["value"] >= 0
    sscx_morphometrics_dict = factsheet_builder.factsheet_dict()

    with open("tests/unit_tests/data/sscx_morphometrics.json", "r") as in_file:
        morphometrics_gt = json.load(in_file)

    assert sscx_morphometrics_dict == morphometrics_gt


def test_hippocampus_morphology_factsheet_builder():
    """Test hippocampus morphology factsheet builder class."""
    factsheet_builder = morphology_features.HippocampusMorphologyFactsheetBuilder(
        test_morph
    )
    morph_features = factsheet_builder.get_feature_values()
    assert len(morph_features) == 51
    for feature in morph_features:
        assert feature["value"] >= 0
    hipp_morphometrics_dict = factsheet_builder.factsheet_dict()

    with open("tests/unit_tests/data/hippocampus_morphometrics.json", "r") as in_file:
        morphometrics_gt = json.load(in_file)

    assert hipp_morphometrics_dict == morphometrics_gt


def test_thalamus_morphology_factsheet_builder():
    """Test thalamus morphology factsheet builder class."""
    factsheet_builder = morphology_features.ThalamusMorphologyFactsheetBuilder(
        test_morph
    )
    morph_features = factsheet_builder.get_feature_values()
    assert len(morph_features) == 12
    for feature in morph_features:
        assert feature["value"] >= 0
    thal_morphometrics_dict = factsheet_builder.factsheet_dict()
    with open("tests/unit_tests/data/thalamus_morphometrics.json", "r") as in_file:
        morphometrics_gt = json.load(in_file)

    assert thal_morphometrics_dict == morphometrics_gt


def test_average_diameter():
    """Test average diameter feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.AverageDiameter(
        morphology, "basal_dendrite", NeuriteType.basal_dendrite
    )
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "average diameter of basal_dendrite"
    assert abs(feature_dict["value"] - 0.6784688234329224) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m"


def test_total_length():
    """Test total length morphology feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalLength(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon length"
    assert abs(feature_dict["value"] - 6365.762633562088) <= 1e-3
    assert feature_dict["unit"] == "\u00b5m"


def test_total_height():
    """Test total height feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalHeight(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon height"
    assert abs(feature_dict["value"] - 1469.0793) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m"


def test_total_width():
    """Test total width feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalWidth(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon width"
    assert abs(feature_dict["value"] - 1840.9316) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m"


def test_total_depth():
    """Test total depth feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalDepth(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon depth"
    assert abs(feature_dict["value"] - 482.443) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m"


def test_total_area():
    """Test the total area feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalArea(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon area"
    assert abs(feature_dict["value"] - 7975.952834655143) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m\u00b2"


def test_total_volume():
    """Test the total volume feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.TotalVolume(morphology, "axon", NeuriteType.axon)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "total axon volume"
    assert abs(feature_dict["value"] - 900.0448369230417) <= 1e-4
    assert feature_dict["unit"] == "\u00b5m\u00b3"


def test_number_of_sections():
    """Test number of sections feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.NumberOfSections(
        morphology, "basal_dendrite", NeuriteType.basal_dendrite
    )
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "number of basal_dendrite sections"
    assert feature_dict["value"] == 33
    assert feature_dict["unit"] == ""


def test_mean_neurite_volumes():
    """Test neurite volumes feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.MeanNeuriteVolumes(
        morphology, "axon", NeuriteType.axon
    )
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "mean axon volume"
    assert abs(feature_dict["value"] - 900.0448369230417) <= 1e-3
    assert feature_dict["unit"] == "\u00b5m\u00b3"


def test_max_branch_order():
    """Test max branch order feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.MaxBranchOrder(
        morphology, "apical_dendrite", NeuriteType.apical_dendrite
    )
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "apical_dendrite maximum branch order"
    assert feature_dict["value"] == 7
    assert feature_dict["unit"] == ""


def test_max_section_length():
    """Test max section length feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.MaxSectionLength(
        morphology, "basal_dendrite", NeuriteType.basal_dendrite
    )
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "basal_dendrite maximum section length"
    assert abs(feature_dict["value"] - 130.07133) <= 1e-5
    assert feature_dict["unit"] == "\u00b5m"


def test_soma_diameter():
    """Test the some diameter feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.SomaDiamater(morphology)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "soma diameter"
    assert abs(feature_dict["value"] - 18.222522735595703) <= 1e-5
    assert feature_dict["unit"] == "\u00b5m"


def test_soma_surface_area():
    """Test the soma surface area feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.SomaSurfaceArea(morphology)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "soma surface area"
    assert abs(feature_dict["value"] - 1043.1983085111349) <= 1e-5
    assert feature_dict["unit"] == "\u00b5m\u00b2"


def test_soma_volume():
    """Test the soma volume feature."""
    morphology = nm.load_neuron(test_morph)
    feature = morphology_features.SomaVolume(morphology)
    feature_dict = feature.to_dict()
    assert feature_dict["name"] == "soma volume"
    assert abs(feature_dict["value"] - 3168.2841490965225) <= 1e-5
    assert feature_dict["unit"] == "\u00b5m\u00b3"
