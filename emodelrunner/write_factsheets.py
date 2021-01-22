"""Produce a me-type data json file."""
import argparse
import collections
import json
import logging
import os
import numpy as np
import re

import efel
import neurom as nm

from emodelrunner.load import find_param_file, load_config, load_params
from emodelrunner.json_loader import json_load

logger = logging.getLogger(__name__)


class NpEncoder(json.JSONEncoder):
    """Class to encode np.integer as python int."""

    def default(self, o):
        """Convert numpy integer to int."""
        if isinstance(o, np.integer):
            return int(o)
        else:
            return super(NpEncoder, self).default(o)


def base_dict(unit, name, value):
    """Basic dictionary for building the me-type json file."""
    return {"unit": unit, "name": name, "value": value, "tooltip": ""}


def get_morph_path(config):
    """Return path to morphology file."""
    # get morphology path from constants
    constants_path = os.path.join(
        config.get("Paths", "constants_dir"), config.get("Paths", "constants_file")
    )
    with open(constants_path, "r") as f:
        data = json.load(f)
    morph_dir = data["morph_dir"]
    morph_fname = data["morph_fname"]

    # change it if it is specified in config file
    if config.has_option("Paths", "morph_dir"):
        morph_dir = config.get("Paths", "morph_dir")
    else:
        morph_dir = os.path.join(config.get("Paths", "memodel_dir"), morph_dir)
    if config.has_option("Paths", "morph_file"):
        morph_fname = config.get("Paths", "morph_file")

    return os.path.join(morph_dir, morph_fname)


def get_neurite_list(nrn):
    """Return neurite names (str) and types (neurom type).

    If basal or apical are not present, name them 'dendrite'.
    """
    api = nm.get("total_length", nrn, neurite_type=nm.APICAL_DENDRITE)
    bas = nm.get("total_length", nrn, neurite_type=nm.BASAL_DENDRITE)
    if api and bas:
        return ["axon", "apical", "basal"], [
            nm.AXON,
            nm.APICAL_DENDRITE,
            nm.BASAL_DENDRITE,
        ]
    elif api and not bas:
        return ["axon", "dendrite"], [nm.AXON, nm.APICAL_DENDRITE]
    elif bas and not api:
        return ["axon", "dendrite"], [nm.AXON, nm.BASAL_DENDRITE]
    logger.warning("No dendrite found!")
    return ["axon"], [nm.AXON]


def get_morph_data(config):
    """Return the morphological data in a dictionary."""
    # get morph path
    morph_path = get_morph_path(config)

    # extract data
    values = []
    nrn = nm.load_neuron(morph_path)
    neurite_names, neurite_types = get_neurite_list(nrn)

    for n_name, n_type in zip(neurite_names, neurite_types):
        leng = nm.get("total_length", nrn, neurite_type=n_type)
        # to avoid error when there is no neurite
        if len(leng) == 0:
            leng = [0]
        length = base_dict("\u00b5m", "total {} length".format(n_name), leng[0])
        values.append(length)

        vol = nm.get("neurite_volumes", nrn, neurite_type=n_type)
        if len(vol) == 0:
            vol = [0]
        volume = base_dict("\u00b5m\u00b3", "total {} volume".format(n_name), vol[0])
        values.append(volume)

        branch_order = nm.get("section_branch_orders", nrn, neurite_type=n_type)
        if len(branch_order) == 0:
            branch_order = [0]
        max_branch_order = base_dict(
            "", "{} maximum branch order".format(n_name), max(branch_order)
        )
        values.append(max_branch_order)

        sec_len = nm.get("section_lengths", nrn, neurite_type=n_type)
        if len(sec_len) == 0:
            sec_len = [0]
        max_section_length = base_dict(
            "\u00b5m", "{} maximum section length".format(n_name), max(sec_len)
        )
        values.append(max_section_length)

    soma_r = nm.get("soma_radii", nrn)
    soma_diam = base_dict("\u00b5m", "soma diameter", 2 * soma_r[0])
    values.append(soma_diam)

    return {"values": values, "name": "Anatomy"}


def get_physiology_data(config):
    """Analyse the output of the RmpRiTau protocol."""
    # get parameters from config
    step_number = config.getint("Protocol", "run_step_number")
    stim_start = config.getint("Protocol", "stimulus_delay")
    stim_duration = config.getint("Protocol", "stimulus_duration")
    amp_filename = os.path.join(
        config.get("Paths", "protocol_amplitudes_dir"),
        config.get("Paths", "protocol_amplitudes_file"),
    )

    # get current amplitude data
    with open(amp_filename, "r") as f:
        data = json.load(f)
    current_amplitude = data["amps"][step_number - 1]

    # get data from run.py output
    fname = "soma_voltage_step{}.dat".format(step_number)
    fpath = os.path.join("python_recordings", fname)
    data = np.loadtxt(fpath)

    # Prepare the trace data
    trace = {}
    trace["T"] = data[:, 0]  # time
    trace["V"] = data[:, 1]  # soma voltage
    trace["stim_start"] = [stim_start]
    trace["stim_end"] = [stim_start + stim_duration]

    # Calculate the necessary eFeatures
    efel_results = efel.getFeatureValues(
        [trace],
        [
            "voltage_base",
            "steady_state_voltage_stimend",
            "decay_time_constant_after_stim",
        ],
    )

    voltage_base = efel_results[0]["voltage_base"][0]
    dct = efel_results[0]["decay_time_constant_after_stim"][0]

    # Calculate input resistance
    trace["decay_start_after_stim"] = efel_results[0]["voltage_base"]
    trace["stimulus_current"] = [current_amplitude]
    efel_results = efel.getFeatureValues([trace], ["ohmic_input_resistance_vb_ssse"])
    input_resistance = efel_results[0]["ohmic_input_resistance_vb_ssse"][0]

    # build dictionary to be returned
    names = ["resting membrane potential", "input resistance", "membrane time constant"]
    vals = [voltage_base, input_resistance, dct]
    units = ["mV", "MOhm", "ms"]
    values = []
    for name, val, unit in zip(names, vals, units):
        data = base_dict(unit, name, val)
        values.append(data)

    return {"values": values, "name": "Physiology"}


def edit_dist_func(value):
    """Edit function expression to be latex and plot readable.

    Args:
        value (str): the distribution function expressed as a string.
            ex: "(-0.8696 + 2.087*math.exp((x)*0.0031))*3.1236056887012746e-06"

    Returns:
        latex (str): a latex-compatible version of the distrib. function
            ex: "(-0.8696 + 2.087*e^{x*0.0031})*3.1236056887012746e-06"
        value (str): a plottable version of the distrib. function
            ex: "(-0.8696 + 2.087exp(x*0.0031))*3.1236056887012746e-06"
    """
    if "math" in value:
        value = value.replace("math.", "")
    if "(x)" in value:
        value = value.replace("(x)", "x")
    latex = re.sub(r"exp*\(([0-9x*-.]*)\)", "e^{\\1}", value)
    return latex, value


def get_param_data(config):
    """Returns final params, param data by section, exponential function expression."""
    # get emodel
    emodel = get_emodel(config)

    # get params file
    recipes_path = "/".join(
        (config.get("Paths", "recipes_dir"), config.get("Paths", "recipes_file"))
    )
    params_filepath = find_param_file(recipes_path, emodel)

    params_path = "/".join((config.get("Paths", "params_dir"), config.get("Paths", "params_file")))
    release_params = load_params(params_path=params_path, emodel=emodel)

    definitions = json_load(params_filepath)

    decay_func = None
    if "decay" in definitions["distributions"].keys():
        decay_func = definitions["distributions"]["decay"]["fun"]

    return (
        release_params,
        definitions["parameters"],
        definitions["distributions"]["exp"]["fun"],
        decay_func,
    )


def get_channel_and_equations(name, param_config, value, exp_fun, decay_fun, decay_cst):
    """Returns the channel and a dictionary containing equation type (uniform or exp) and value.

    Args:
        name (str): the name of the ion channel and its parameter.
            should have the form parameter_channel (ex: "gCa_HVAbar_Ca_HVA2")
        param_config (dict): parameter dictionary taken from parameter data file.
            should have a "dist" key if the distribution is exponential.
        value (float): parameter value (obtained from optimisation).
        exp_fun (str): the distribution function expressed as a string.
            ex: "(-0.8696 + 2.087*math.exp((x)*0.0031))*3.1236056887012746e-06"

    Returns:
        channel (str): name of the channel (ex: "Ca_HVA2")
        biophys (str): parameter name (ex: "gCa_HVAbar")
        equations (dict): dictionary containing equation values (for plotting and latex display)
            and type (uniform or exponential)
    """
    # isolate channel and biophys
    split_name = name.split("_")
    if len(split_name) == 4:
        biophys = "_".join(split_name[0:2])
        channel = "_".join(split_name[2:4])
    elif len(split_name) == 3:
        biophys = split_name[0]
        channel = "_".join(split_name[1:3])
    elif len(split_name) == 2:
        biophys = split_name[0]
        channel = split_name[1]

    # type
    if "dist" in param_config:
        if param_config["dist"] == "exp":
            type_ = "exponential"
            value = exp_fun.format(distance="x", value=value)
            latex, plot = edit_dist_func(value)
        elif param_config["dist"] == "decay":
            type_ = "decay"
            value = decay_fun.format(distance="x", value=value, constant=decay_cst)
            latex, plot = edit_dist_func(value)
        else:
            logger.warning(
                "dist is set to {}.".format(param_config["dist"])
                + " Expected 'exp' or 'decay'. Set type to exponential anyway."
            )
    else:
        type_ = "uniform"
        latex = value
        plot = value

    return channel, biophys, {"latex": latex, "plot": plot, "type": type_}


def get_mechanisms_data(config):
    """Return a dictionary containing channel mechanisms for each section."""
    release_params, parameters, exp_fun, decay_fun = get_param_data(config)
    decay_cst = None
    if decay_fun:
        decay_cst = release_params["constant.distribution_decay"]

    dendrite = {"channels": {}}
    apical = {"channels": {}}
    basal = {"channels": {}}
    axonal = {"channels": {}}
    somatic = {"channels": {}}

    for section, params in parameters.items():
        # do not take into account "comment"
        if isinstance(params, list):
            for param_config in params:
                name = param_config["name"]
                full_name = ".".join((name, section))

                # only take into account parameters present in finals.json
                if full_name in release_params and full_name != "constant.distribution_decay":
                    value = release_params[full_name]
                    channel, biophys, equation_dict = get_channel_and_equations(
                        name, param_config, value, exp_fun, decay_fun, decay_cst
                    )

                    # do not take into account "all" section
                    # set default to create keys then add equations
                    # this allows to either create channel data or append to channel key
                    if section == "alldend":
                        dendrite["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        dendrite["channels"][channel]["equations"][biophys] = equation_dict
                    elif section == "somadend":
                        dendrite["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        dendrite["channels"][channel]["equations"][biophys] = equation_dict
                        somatic["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        somatic["channels"][channel]["equations"][biophys] = equation_dict
                    elif section == "somaxon":
                        somatic["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        somatic["channels"][channel]["equations"][biophys] = equation_dict
                        axonal["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        axonal["channels"][channel]["equations"][biophys] = equation_dict
                    elif section == "allact":
                        dendrite["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        dendrite["channels"][channel]["equations"][biophys] = equation_dict
                        somatic["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        somatic["channels"][channel]["equations"][biophys] = equation_dict
                        axonal["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        axonal["channels"][channel]["equations"][biophys] = equation_dict
                    elif section == "apical":
                        apical["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        apical["channels"][channel]["equations"][biophys] = equation_dict
                    elif section == "basal":
                        basal["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        basal["channels"][channel]["equations"][biophys] = equation_dict
                    elif section == "axonal":
                        axonal["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        axonal["channels"][channel]["equations"][biophys] = equation_dict
                    elif section == "somatic":
                        somatic["channels"].setdefault(
                            channel, {"equations": {biophys: equation_dict}}
                        )
                        somatic["channels"][channel]["equations"][biophys] = equation_dict

    location_map = {}
    locs = [dendrite, apical, basal, somatic, axonal]
    loc_names = ["all dendrites", "apical", "basal", "somatic", "axonal"]
    for loc_name, loc in zip(loc_names, locs):
        if loc["channels"]:
            location_map[loc_name] = loc

    values = [
        {
            "tooltip": "",
            "location_map": location_map,
            "unit": "",
            "name": "list of ion channel mechanisms",
        }
    ]
    return {"values": values, "name": "Channel mechanisms"}


def get_emodel(config):
    """Returns emodel as a string."""
    # get emodel
    constants_path = os.path.join(
        config.get("Paths", "constants_dir"), config.get("Paths", "constants_file")
    )
    with open(constants_path, "r") as f:
        data = json.load(f)

    return data["template_name"]


def get_recipe(config, emodel):
    """Get recipe dict."""
    # get features path
    recipes_path = "/".join(
        (config.get("Paths", "recipes_dir"), config.get("Paths", "recipes_file"))
    )
    recipes = json_load(recipes_path)

    return recipes[emodel]


def load_raw_exp_features(recipe):
    """Load experimental features from file."""
    features_path = recipe["features"]

    return json_load(features_path)


def load_feature_units():
    """Load dict with 'feature_name': 'unit' for all features."""
    unit_json_path = "/".join(("config", "features", "units.json"))

    return json_load(unit_json_path)


def load_fitness(config, emodel):
    """Load dict containing model fitness value for each feature."""
    params_path = "/".join((config.get("Paths", "params_dir"), config.get("Paths", "params_file")))
    params_file = json_load(params_path)
    data = params_file[emodel]

    return data["fitness"]


def get_prefix(config, recipe):
    """Get the prefix used in the fitness keys (e.g. '_' or 'L5TPCa')."""
    return recipe["morphology"][0][0]


def get_exp_features_data(config):
    """Returns a dict containing mean and std of experimental features and model fitness."""
    emodel = get_emodel(config)
    recipe = get_recipe(config, emodel)
    feat = load_raw_exp_features(recipe)
    units = load_feature_units()
    fitness = load_fitness(config, emodel)
    prefix = get_prefix(config, recipe)

    values_dict = {}
    for stimulus, stim_data in feat.items():
        stim_dict = {}
        for location, loc_data in stim_data.items():
            features_list = []
            for feature in loc_data:
                feature_name = feature["feature"]
                mean = feature["val"][0]
                std = feature["val"][1]

                try:
                    unit = units[feature_name]
                except KeyError:
                    logger.warning(
                        "{} was not found in units file. Set unit to ''.".format(feature_name)
                    )
                    unit = ""

                key_fitness = ".".join((prefix, stimulus, location, feature_name))
                try:
                    fit = fitness[key_fitness]
                except KeyError:
                    logger.warning(
                        "{} was not found in fitness dict. ".format(key_fitness)
                        + "Set fitness model fitness value to ''."
                    )
                    fit = ""

                features_list.append(
                    {
                        "name": feature_name,
                        "values": [{"mean": mean, "std": std}],
                        "unit": unit,
                        "model fitness": fit,
                        "tooltip": "",
                    }
                )
            loc_dict = {"features": features_list}
            stim_dict[location] = loc_dict
        values_dict[stimulus] = stim_dict
    values = [values_dict]

    return {"values": values, "name": "Experimental features"}


def get_morph_name(config):
    """Returns a dict containing the morphology name."""
    if config.has_option("Paths", "morph_file"):
        morph_fname = config.get("Paths", "morph_file")
    else:
        constants_path = os.path.join(
            config.get("Paths", "constants_dir"), config.get("Paths", "constants_file")
        )
        with open(constants_path, "r") as f:
            data = json.load(f)
        morph_fname = data["morph_fname"]
    morph_name = morph_fname.split(".asc")[0]

    return {"value": morph_name, "name": "Morphology name"}


def write_etype_json(config, output_dir="."):
    """Write the e-type factsheet json file."""
    exp_features = get_exp_features_data(config)
    channel_mechanisms = get_mechanisms_data(config)
    morphology_name = get_morph_name(config)
    # TODO exp_traces = get_exp_traces_data(config)

    output = [
        exp_features,
        channel_mechanisms,
        morphology_name,
        # TODO exp_traces,
    ]

    output_fname = "e_type_factsheeet.json"
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    with open(os.path.join(output_dir, output_fname), "w") as out_file:
        json.dump(output, out_file, indent=4, cls=NpEncoder)
    print("e-type json file written.")


def write_morph_json(config, output_dir="."):
    """Write the morphology factsheet json file."""
    anatomy = get_morph_data(config)
    morphology_name = get_morph_name(config)

    output = [anatomy, morphology_name]

    output_fname = "morphology_factsheeet.json"
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    with open(os.path.join(output_dir, output_fname), "w") as out_file:
        json.dump(output, out_file, indent=4, cls=NpEncoder)
    print("morph json file written.")


def write_metype_json(config, output_dir="."):
    """Write the me-type factsheet json file."""
    anatomy = get_morph_data(config)
    physiology = get_physiology_data(config)
    morphology_name = get_morph_name(config)

    output = [anatomy, physiology, morphology_name]

    output_fname = "me_type_factsheeet.json"
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    with open(os.path.join(output_dir, output_fname), "w") as out_file:
        json.dump(output, out_file, indent=4, cls=NpEncoder)
    print("me-type json file written.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--c",
        default=None,
        help="the name of the config file",
    )
    args = parser.parse_args()

    config_file = args.c
    config = load_config(filename=config_file)

    output_dir = "factsheets"
    write_metype_json(config, output_dir)
    write_etype_json(config, output_dir)
    write_morph_json(config, output_dir)
