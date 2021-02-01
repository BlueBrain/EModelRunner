"""Produce a me-type data json file."""

# pylint: disable=super-with-arguments
import argparse
import json
import logging
import os
import re
import numpy as np

import efel
import neurom as nm

from emodelrunner.load import find_param_file, load_config, load_params, load_amps
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


def create_neurite_len_dict(nrn, n_type, n_name):
    """Return a dict containing total neurite length."""
    leng = nm.get("total_length", nrn, neurite_type=n_type)
    # to avoid error when there is no neurite
    if len(leng) == 0:
        leng = [0]
    return base_dict("\u00b5m", "total {} length".format(n_name), leng[0])


def create_neurite_vol_dict(nrn, n_type, n_name):
    """Return a dict containing total neurite volume."""
    vol = nm.get("neurite_volumes", nrn, neurite_type=n_type)
    # to avoid error when there is no neurite
    if len(vol) == 0:
        vol = [0]
    return base_dict("\u00b5m\u00b3", "total {} volume".format(n_name), vol[0])


def create_neurite_max_bo_dict(nrn, n_type, n_name):
    """Return a dict containing maximum neurite branch order."""
    branch_order = nm.get("section_branch_orders", nrn, neurite_type=n_type)
    # to avoid error when there is no neurite
    if len(branch_order) == 0:
        branch_order = [0]
    return base_dict("", "{} maximum branch order".format(n_name), max(branch_order))


def create_neurite_max_sec_len_dict(nrn, n_type, n_name):
    """Return a dict containing maximum neurite section length."""
    sec_len = nm.get("section_lengths", nrn, neurite_type=n_type)
    # to avoid error when there is no neurite
    if len(sec_len) == 0:
        sec_len = [0]
    return base_dict(
        "\u00b5m", "{} maximum section length".format(n_name), max(sec_len)
    )


def create_soma_diam_dict(nrn):
    """Return a dict containing soma diameter."""
    soma_r = nm.get("soma_radii", nrn)
    return base_dict("\u00b5m", "soma diameter", 2 * soma_r[0])


def get_morph_data(config):
    """Return the morphological data in a dictionary."""
    # get morph path
    morph_path = get_morph_path(config)

    # extract data
    values = []
    nrn = nm.load_neuron(morph_path)
    neurite_names, neurite_types = get_neurite_list(nrn)

    for n_name, n_type in zip(neurite_names, neurite_types):
        length = create_neurite_len_dict(nrn, n_type, n_name)
        values.append(length)

        volume = create_neurite_vol_dict(nrn, n_type, n_name)
        values.append(volume)

        max_branch_order = create_neurite_max_bo_dict(nrn, n_type, n_name)
        values.append(max_branch_order)

        max_section_length = create_neurite_max_sec_len_dict(nrn, n_type, n_name)
        values.append(max_section_length)

    soma_diam = create_soma_diam_dict(nrn)
    values.append(soma_diam)

    return {"values": values, "name": "Anatomy"}


def get_trace_data(config):
    """Return trace dict for efel feature computing."""
    # get parameters from config
    step_number = config.getint("Protocol", "run_step_number")
    stim_start = config.getint("Protocol", "stimulus_delay")
    stim_duration = config.getint("Protocol", "stimulus_duration")

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

    return trace


def get_input_resistance(efel_results, trace, config):
    """Return input resistance from efel."""
    step_number = config.getint("Protocol", "run_step_number")
    amps, _ = load_amps(config)
    current_amplitude = amps[step_number - 1]

    # Calculate input resistance
    trace["decay_start_after_stim"] = efel_results[0]["voltage_base"]
    trace["stimulus_current"] = [current_amplitude]
    efel_results = efel.getFeatureValues([trace], ["ohmic_input_resistance_vb_ssse"])
    return efel_results[0]["ohmic_input_resistance_vb_ssse"][0]


def get_physiology_data(config):
    """Analyse the output of the RmpRiTau protocol."""
    trace = get_trace_data(config)

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
    input_resistance = get_input_resistance(efel_results, trace, config)

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

    params_path = "/".join(
        (config.get("Paths", "params_dir"), config.get("Paths", "params_file"))
    )
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


def get_channel_and_equations(
    name, param_config, full_name, exp_fun, decay_fun, release_params
):
    """Returns the channel and a dictionary containing equation type (uniform or exp) and value.

    Args:
        name (str): the name of the ion channel and its parameter.
            should have the form parameter_channel (ex: "gCa_HVAbar_Ca_HVA2")
        param_config (dict): parameter dictionary taken from parameter data file.
            should have a "dist" key if the distribution is exponential.
        full_name (str): should have the form name.section
        exp_fun (str): the distribution function expressed as a string.
            ex: "(-0.8696 + 2.087*math.exp((x)*0.0031))*3.1236056887012746e-06"
        decay_fun (str): the decay function expressed as a string.
        release_params (dict): final parameters of the optimised cell.

    Returns:
        channel (str): name of the channel (ex: "Ca_HVA2")
        biophys (str): parameter name (ex: "gCa_HVAbar")
        equations (dict): dictionary containing equation values (for plotting and latex display)
            and type (uniform or exponential)
    """
    # parameter value (obtained from optimisation)
    value = release_params[full_name]

    decay_cst = None
    if decay_fun:
        decay_cst = release_params["constant.distribution_decay"]

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
                "dist is set to %s. Expected 'exp' or 'decay'. Set type to exponential anyway.",
                param_config["dist"],
            )
    else:
        type_ = "uniform"
        latex = value
        plot = value

    return channel, biophys, {"latex": latex, "plot": plot, "type": type_}


def append_equation(location_map, section, channel, biophys, equation_dict):
    """Append equation to location map dict."""
    # do not take into account "all" section
    # set default to create keys then add equations
    # this allows to either create channel data or append to channel key
    if section == "alldend":
        location_map["all dendrites"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["all dendrites"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "somadend":
        location_map["all dendrites"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["all dendrites"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
        location_map["somatic"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["somatic"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "somaxon":
        location_map["somatic"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["somatic"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
        location_map["axonal"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["axonal"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "allact":
        location_map["all dendrites"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["all dendrites"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
        location_map["somatic"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["somatic"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
        location_map["axonal"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["axonal"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "apical":
        location_map["apical"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["apical"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "basal":
        location_map["basal"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["basal"]["channels"][channel]["equations"][biophys] = equation_dict
    elif section == "axonal":
        location_map["axonal"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["axonal"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "somatic":
        location_map["somatic"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["somatic"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict


def clean_location_map(location_map):
    """Remove empty locations."""
    for key, loc in list(location_map.items()):
        if not loc["channels"]:
            location_map.pop(key)


def get_mechanisms_data(config):
    """Return a dictionary containing channel mechanisms for each section."""
    release_params, parameters, exp_fun, decay_fun = get_param_data(config)

    location_map = {
        "all dendrites": {"channels": {}},
        "apical": {"channels": {}},
        "basal": {"channels": {}},
        "somatic": {"channels": {}},
        "axonal": {"channels": {}},
    }

    for section, params in parameters.items():
        # do not take into account "comment"
        if isinstance(params, list):
            for param_config in params:
                name = param_config["name"]
                full_name = ".".join((name, section))

                # only take into account parameters present in finals.json
                if (
                    full_name in release_params
                    and full_name != "constant.distribution_decay"
                ):
                    channel, biophys, equation_dict = get_channel_and_equations(
                        name,
                        param_config,
                        full_name,
                        exp_fun,
                        decay_fun,
                        release_params,
                    )

                    # append equation in location map
                    append_equation(
                        location_map, section, channel, biophys, equation_dict
                    )

    # remove empty locations
    clean_location_map(location_map)

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
    params_path = "/".join(
        (config.get("Paths", "params_dir"), config.get("Paths", "params_file"))
    )
    params_file = json_load(params_path)
    data = params_file[emodel]

    return data["fitness"]


def get_prefix(recipe):
    """Get the prefix used in the fitness keys (e.g. '_' or 'L5TPCa')."""
    return recipe["morphology"][0][0]


def get_feature_dict(feature, units, prefix, stimulus, location, fitness):
    """Return dict containing one feature."""
    feature_name = feature["feature"]
    mean = feature["val"][0]
    std = feature["val"][1]

    try:
        unit = units[feature_name]
    except KeyError:
        logger.warning("%s was not found in units file. Set unit to ''.", feature_name)
        unit = ""

    key_fitness = ".".join((prefix, stimulus, location, feature_name))
    try:
        fit = fitness[key_fitness]
    except KeyError:
        logger.warning(
            "%s was not found in fitness dict. Set fitness model fitness value to ''.",
            key_fitness,
        )
        fit = ""

    return {
        "name": feature_name,
        "values": [{"mean": mean, "std": std}],
        "unit": unit,
        "model fitness": fit,
        "tooltip": "",
    }


def get_exp_features_data(config):
    """Returns a dict containing mean and std of experimental features and model fitness."""
    # pylint: disable=too-many-locals
    # it is hard to reduce number of locals without reducing readibility
    emodel = get_emodel(config)
    recipe = get_recipe(config, emodel)

    feat = load_raw_exp_features(recipe)
    units = load_feature_units()
    fitness = load_fitness(config, emodel)
    prefix = get_prefix(recipe)

    values_dict = {}
    for stimulus, stim_data in feat.items():
        stim_dict = {}
        for location, loc_data in stim_data.items():
            features_list = []
            for feature in loc_data:
                features_list.append(
                    get_feature_dict(
                        feature, units, prefix, stimulus, location, fitness
                    )
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
    config_ = load_config(filename=config_file)

    output_dir_ = "factsheets"
    write_metype_json(config_, output_dir_)
    write_etype_json(config_, output_dir_)
    write_morph_json(config_, output_dir_)
