"""Unit tests for the factsheets output."""

from pathlib import Path
import json

import numpy as np

from emodelrunner.load import load_config
from emodelrunner.run import main as run_emodel
from emodelrunner.factsheets import morphology_features
from emodelrunner.factsheets.output import (
    write_metype_json_from_config,
    write_emodel_json,
)
from emodelrunner.factsheets.physiology_features import physiology_factsheet_info
from tests.utils import cwd


example_dir = Path(".") / "examples" / "sscx_sample_dir"


class TestMETypeFactsheet:
    """Test the metype factsheet."""

    @classmethod
    def setup_class(cls):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        configfile = example_dir / "config" / "config_singlestep.ini"
        config = load_config(config_dir=configfile.parent, filename=configfile.name)
        cls.output_path = example_dir / "factsheets" / "me_type_factsheet.json"

        with cwd(example_dir):
            run_emodel(config_file="config_singlestep.ini")

        voltage_path = (
            Path(example_dir) / "python_recordings" / "soma_voltage_step1.dat"
        )
        morphology_path = (
            Path(example_dir)
            / "morphology"
            / "dend-C270999B-P3_axon-C060110A3_-_Scale_x1.000_y0.950_z1.000.asc"
        )
        assert morphology_path.is_file()
        write_metype_json_from_config(
            config, voltage_path, morphology_path, cls.output_path
        )

    def test_metype_factsheet_exists(self):
        """Test if the factsheet file is created."""
        assert self.output_path.is_file()


def test_emodel_factsheet_output():
    """Tests if the emodel factsheet output file is created."""
    configfile = example_dir / "config" / "config_singlestep.ini"
    config = load_config(config_dir=configfile.parent, filename=configfile.name)

    output_path = example_dir / "factsheets" / "e_model_factsheet.json"
    emodel = config.get("Cell", "emodel")

    recipes_path = Path(example_dir) / "emodel_parameters" / "recipe.json"

    with open(recipes_path) as json_file:
        recipes_dict = json.load(json_file)

    unoptimized_params_path = (
        Path(example_dir) / "emodel_parameters" / "params" / "pyr.json"
    )
    with open(unoptimized_params_path) as json_file:
        unoptimized_params_dict = json.load(json_file)

    optimized_params_path = (
        Path(example_dir) / "emodel_parameters" / "params" / "final.json"
    )
    with open(optimized_params_path) as json_file:
        optimized_params_dict = json.load(json_file)

    features_path = (
        Path(example_dir) / "emodel_parameters" / "features" / "cADpyr_L5PC.json"
    )
    with open(features_path) as json_file:
        features_dict = json.load(json_file)

    feature_units_path = (
        Path(example_dir) / "emodel_parameters" / "features" / "units.json"
    )
    with open(feature_units_path) as json_file:
        feature_units_dict = json.load(json_file)

    write_emodel_json(
        emodel,
        recipes_dict,
        features_dict,
        feature_units_dict,
        unoptimized_params_dict,
        optimized_params_dict,
        output_path,
    )

    assert output_path.is_file()


def test_anatomy_features():
    """Checks that all anatomy data is positive and exists.

    Fields include axon and soma.
    Fields can either include basal and apical, or just dendrite.

    Checks that there is no empty list or dict.
    Checks that data exists and is a float/int and is positive.
    Checks that there is no anatomy field missing.
    """
    morphology_path = (
        Path(example_dir)
        / "morphology"
        / "dend-C270999B-P3_axon-C060110A3_-_Scale_x1.000_y0.950_z1.000.asc"
    )

    morph_factsheet_builder = morphology_features.MorphologyFactsheetBuilder(
        morphology_path
    )

    ana_dict = morph_factsheet_builder.get_all_feature_values()
    ana_dict = {"values": ana_dict, "name": "Anatomy"}
    left_to_check_1 = [
        "total axon length",
        "mean axon volume",
        "axon maximum branch order",
        "axon maximum section length",
        "total apical length",
        "mean apical volume",
        "apical maximum branch order",
        "apical maximum section length",
        "total basal length",
        "mean basal volume",
        "basal maximum branch order",
        "basal maximum section length",
        "soma diameter",
    ]
    left_to_check_2 = [
        "total axon length",
        "mean axon volume",
        "axon maximum branch order",
        "axon maximum section length",
        "total dendrite length",
        "mean dendrite volume",
        "dendrite maximum branch order",
        "dendrite maximum section length",
        "soma diameter",
    ]
    lists_to_check = [left_to_check_1, left_to_check_2]

    assert ana_dict["values"]
    for item in ana_dict["values"]:
        assert isinstance(item["value"], (float, int, np.floating, np.integer))
        assert item["value"] > 0

        for l in lists_to_check:
            if item["name"] in l:
                l.remove(item["name"])

    assert len(lists_to_check[0]) == 0 or len(lists_to_check[1]) == 0


def test_physiology_features():
    """Checks that all physiology values exist.

    Checks that there is no empty list or dict.
    Checks that data exists and is a float and is positive (except for membrane pot.).
    Checks that there is no physiology field missing.
    """
    configfile = example_dir / "config" / "config_singlestep.ini"
    config = load_config(config_dir=configfile.parent, filename=configfile.name)
    # get current amplitude
    step_number = config.getint("Protocol", "run_step_number")
    stim_name = "stimulus_amp" + str(step_number)
    current_amplitude = config.getfloat("Protocol", stim_name)

    # get parameters from config
    stim_start = config.getint("Protocol", "stimulus_delay")
    stim_duration = config.getint("Protocol", "stimulus_duration")

    # get data path from run.py output
    voltage_path = Path(example_dir) / "python_recordings" / "soma_voltage_step1.dat"
    data = np.loadtxt(voltage_path)

    phys_dict = physiology_factsheet_info(
        time=data[:, 0],
        voltage=data[:, 1],
        current_amplitude=current_amplitude,
        stim_start=stim_start,
        stim_duration=stim_duration,
    )
    left_to_check = [
        "input resistance",
        "membrane time constant",
        "resting membrane potential",
    ]

    assert phys_dict["values"]
    for item in phys_dict["values"]:
        assert isinstance(item["value"], float)
        if item["name"] in ["input resistance", "membrane time constant"]:
            assert item["value"] >= 0
        left_to_check.remove(item["name"])

    assert len(left_to_check) == 0
