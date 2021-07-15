"""Writes the factsheets to the disk."""

import argparse
import json
import logging
import os
import numpy as np

from emodelrunner.load import find_param_file, load_config
from emodelrunner.json_utilities import NpEncoder
from emodelrunner.factsheets.morphology_features import MorphologyFactsheetBuilder
from emodelrunner.factsheets.physiology_features import physiology_factsheet_info
from emodelrunner.factsheets.experimental_features import get_exp_features_data
from emodelrunner.factsheets.ion_channel_mechanisms import get_mechanisms_data

logger = logging.getLogger(__name__)


def get_morph_name_dict(morph_fname):
    """Returns a dict containing the morphology name."""
    morph_name = morph_fname.split(".asc")[0]

    return {"name": "Morphology name", "value": morph_name}


def write_emodel_json(
    emodel, recipes_path, params_filepath, params_path, output_dir="."
):
    """Write the e-model factsheet json file."""
    exp_features = get_exp_features_data(emodel, recipes_path, params_path)
    channel_mechanisms = get_mechanisms_data(emodel, params_path, params_filepath)

    output = [
        exp_features,
        channel_mechanisms,
    ]

    output_fname = "e_model_factsheet.json"
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    with open(os.path.join(output_dir, output_fname), "w") as out_file:
        json.dump(output, out_file, indent=4, cls=NpEncoder)
    print("e-model json file is written.")


def write_emodel_json_from_config(config, output_dir="."):
    """Write the e-model factsheet json file."""
    emodel = config.get("Cell", "emodel")

    recipes_path = "/".join(
        (config.get("Paths", "recipes_dir"), config.get("Paths", "recipes_file"))
    )
    params_filepath = find_param_file(recipes_path, emodel)

    params_path = "/".join(
        (config.get("Paths", "params_dir"), config.get("Paths", "params_file"))
    )

    write_emodel_json(emodel, recipes_path, params_filepath, params_path, output_dir)


def write_metype_json(
    data_path,
    current_amplitude,
    stim_start,
    stim_duration,
    morph_dir,
    morph_fname,
    output_dir=".",
):
    """Write the me-type factsheet json file."""
    # load time, voltage
    data = np.loadtxt(data_path)

    morph_factsheet_builder = MorphologyFactsheetBuilder(
        os.path.join(morph_dir, morph_fname)
    )
    anatomy = morph_factsheet_builder.get_all_feature_values()
    anatomy = {"name": "Anatomy", "values": anatomy}

    physiology = physiology_factsheet_info(
        time=data[:, 0],
        voltage=data[:, 1],
        current_amplitude=current_amplitude,
        stim_start=stim_start,
        stim_duration=stim_duration,
    )
    morphology_name = get_morph_name_dict(morph_fname)

    output = [anatomy, physiology, morphology_name]

    output_fname = "me_type_factsheet.json"
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    with open(os.path.join(output_dir, output_fname), "w") as out_file:
        json.dump(output, out_file, indent=4, cls=NpEncoder)
    print("me-type json file written.")


def write_metype_json_from_config(config, output_dir="."):
    """Write the me-type factsheet json file."""
    # get current amplitude
    step_number = config.getint("Protocol", "run_step_number")
    stim_name = "stimulus_amp" + str(step_number)
    current_amplitude = config.getfloat("Protocol", stim_name)

    # get parameters from config
    stim_start = config.getint("Protocol", "stimulus_delay")
    stim_duration = config.getint("Protocol", "stimulus_duration")

    # get data path from run.py output
    fname = "soma_voltage_step{}.dat".format(step_number)
    fpath = os.path.join("python_recordings", fname)

    # get morph path
    morph_dir = config.get("Paths", "morph_dir")
    morph_fname = config.get("Paths", "morph_file")

    write_metype_json(
        fpath,
        current_amplitude,
        stim_start,
        stim_duration,
        morph_dir,
        morph_fname,
        output_dir,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--c",
        default=None,
        help="the name of the config file",
    )
    args = parser.parse_args()

    config_file = args.c
    config_ = load_config(filename=config_file)

    output_dir_ = "factsheets"
    write_metype_json_from_config(config_, output_dir_)
    write_emodel_json_from_config(config_, output_dir_)
