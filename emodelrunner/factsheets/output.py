"""Functionality to save factsheets output."""

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

import json
from pathlib import Path
import numpy as np

from emodelrunner.json_utilities import NpEncoder
from emodelrunner.factsheets.morphology_features import SSCXMorphologyFactsheetBuilder
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
    """Write the me-type factsheet json file.

    The output metype factsheet contains anatomy, physiology and morphology data.

    Args:
        data_path (str): path to the trace data (usually output of emodelrunner run)
        current_amplitude (float): current amplitude of the stimulus (nA)
        stim_start (float): time at which the stimulus begins (ms)
        stim_duration (float): stimulus duration (ms)
        morphology_path (str or Path): Path to the morphology file.
        output_path (str): path to the metype factsheet output
    """
    morphology_path = Path(morphology_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # load time, voltage
    data = np.loadtxt(data_path)

    morph_factsheet_builder = SSCXMorphologyFactsheetBuilder(morph_path=morphology_path)
    anatomy = morph_factsheet_builder.factsheet_dict()

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


def get_stim_params_from_config_for_physiology_factsheet(prot_path, protocol_key):
    """Get step amplitude, delay and duration for phisiology factsheet.

    Args:
        prot_path (str or Path): path to the json file containing the protocols
        protocol_key (str): name of the protocol used for physiology features extraction

    Returns:
        a tuple containing

        - current_amplitude (int or float): the amplitude current of the step protocol (mA)
        - stim_start (int or float): the start of the stimulus (ms)
        - stim_duration (int or float): the duration of the stimulus (ms)

    Raises:
        Exception: If a step protocol with multiple steps has been provided
    """
    with open(prot_path, "r", encoding="utf-8") as protocol_file:
        protocol_definitions = json.load(protocol_file)

    prot = protocol_definitions[protocol_key]
    step_stim = prot["stimuli"]["step"]

    if isinstance(step_stim, list):
        exception_message = (
            "ME-type factsheet expects only one step stimulus "
            + "for protocol {key} at {filepath}"
        )
        raise Exception(exception_message.format(key=protocol_key, filepath=prot_path))

    # get parameters from protocol
    current_amplitude = step_stim["amp"]
    stim_start = step_stim["delay"]
    stim_duration = step_stim["duration"]

    return current_amplitude, stim_start, stim_duration


def write_metype_json_from_config(
    config, voltage_path, morphology_path, output_path, protocol_key
):
    """Write the me-type factsheet json file.

    Args:
        config (configparser.ConfigParser): configuration
        voltage_path (str): path to the trace data (usually output of emodelrunner run)
        morphology_path (str): Path to the morphology file.
        output_path (str): path to the metype factsheet output
        protocol_key (str): name of the protocol used for physiology features extraction
    """
    # get protocol data
    prot_path = config.get("Paths", "prot_path")

    stim_params = get_stim_params_from_config_for_physiology_factsheet(
        prot_path, protocol_key
    )
    current_amplitude, stim_start, stim_duration = stim_params

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
    morphology_prefix,
    features_dict,
    feature_units_dict,
    unoptimized_params_dict,
    optimized_params_dict,
    output_path,
):
    """Write the e-model factsheet json file.

    The output metype factsheet contains experimental features and channel mechanisms data.

    Args:
        emodel (str): name of the emodel
        morphology_prefix (str): prefix used in the fitness key to the experimental feature
        features_dict (dict): contains the experimental features
        feature_units_dict (dict): contains the units for the experimental features
        unoptimized_params_dict (dict): contains the unoptimized parameters,
            and also contains the decay and exponential equations
        optimized_params_dict (dict): contains the optimized parameters,
            as well as the original morphology path
        output_path (str): path to the e-model factsheet output
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exp_features = get_exp_features_data(
        emodel,
        morphology_prefix,
        features_dict,
        feature_units_dict,
        optimized_params_dict,
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
