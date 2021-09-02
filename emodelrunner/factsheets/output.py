"""Functionality to save factsheets output."""

import json
from pathlib import Path
import numpy as np

from emodelrunner.json_utilities import NpEncoder
from emodelrunner.factsheets.morphology_features import MorphologyFactsheetBuilder
from emodelrunner.factsheets.physiology_features import physiology_factsheet_info
from emodelrunner.factsheets.experimental_features import get_exp_features_data
from emodelrunner.factsheets.ion_channel_mechanisms import get_mechanisms_data


def write_metype_json(
    data_path,
    current_amplitude,
    stim_start,
    stim_duration,
    morphology_path,
    output_path,
):
    """Write the me-type factsheet json file."""
    morphology_path = Path(morphology_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # load time, voltage
    data = np.loadtxt(data_path)

    morph_factsheet_builder = MorphologyFactsheetBuilder(morph_path=morphology_path)
    anatomy = morph_factsheet_builder.get_all_feature_values()
    anatomy = {"name": "Anatomy", "values": anatomy}

    physiology = physiology_factsheet_info(
        time=data[:, 0],
        voltage=data[:, 1],
        current_amplitude=current_amplitude,
        stim_start=stim_start,
        stim_duration=stim_duration,
    )
    morphology = {"name": "Morphology name", "value": morphology_path.stem}

    output = [anatomy, physiology, morphology]

    with open(output_path, "w", encoding="utf-8") as out_file:
        json.dump(output, out_file, indent=4, cls=NpEncoder)
    print("me-type json file written.")


def write_metype_json_from_config(config, voltage_path, morphology_path, output_path):
    """Write the me-type factsheet json file."""
    # get current amplitude
    step_number = config.getint("Protocol", "run_step_number")
    stim_name = "stimulus_amp" + str(step_number)
    current_amplitude = config.getfloat("Protocol", stim_name)

    # get parameters from config
    stim_start = config.getint("Protocol", "stimulus_delay")
    stim_duration = config.getint("Protocol", "stimulus_duration")

    write_metype_json(
        voltage_path,
        current_amplitude,
        stim_start,
        stim_duration,
        morphology_path,
        output_path,
    )


def write_emodel_json(
    emodel,
    recipes_dict,
    features_dict,
    feature_units_dict,
    unoptimized_params_dict,
    optimized_params_dict,
    output_path,
):
    """Write the e-model factsheet json file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exp_features = get_exp_features_data(
        emodel, recipes_dict, features_dict, feature_units_dict, optimized_params_dict
    )
    channel_mechanisms = get_mechanisms_data(
        emodel, optimized_params_dict, unoptimized_params_dict
    )

    output = [
        exp_features,
        channel_mechanisms,
    ]

    with open(output_path, "w", encoding="utf-8") as out_file:
        json.dump(output, out_file, indent=4, cls=NpEncoder)
    print("e-model json file is written.")
