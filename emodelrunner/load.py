"""Functions mainly for loading params for run.py."""

import collections

import json
import os

from bluepyopt import ephys

from emodelrunner.synapses.mechanism import NrnMODPointProcessMechanismCustom
from emodelrunner.locations import multi_locations
from emodelrunner.configuration import SSCXConfigValidator, SynplasConfigValidator


def load_sscx_config(config_path):
    """Validates and returns the configuration file for the SSCX packages.

    Args:
        config_path (str or Path): path to the configuration file.

    Returns:
        configparser.ConfigParser: loaded config object
    """
    conf_validator = SSCXConfigValidator()
    validated_config = conf_validator.validate_from_file(config_path)

    return validated_config


def load_synplas_config(config_path):
    """Validates and returns the configuration file for the Synplas packages.

    Args:
        config_path (str or Path): path to the configuration file.

    Returns:
        configparser.ConfigParser: loaded config object
    """
    conf_validator = SynplasConfigValidator()
    validated_config = conf_validator.validate_from_file(config_path)

    return validated_config


def get_hoc_paths_args(config):
    """Get the dict containing the paths to the hoc files."""
    return {
        "hoc_dir": config.get("Paths", "memodel_dir"),
        "hoc_filename": config.get("Paths", "hoc_file"),
        "simul_hoc_filename": config.get("Paths", "simul_hoc_file"),
        "syn_dir": config.get("Paths", "syn_dir"),
        "syn_dir_for_hoc": config.get("Paths", "syn_dir_for_hoc"),
        "syn_hoc_filename": config.get("Paths", "syn_hoc_file"),
    }


def get_prot_args(config):
    """Get the dict containing recipe protocols configuration data."""
    return {
        "emodel": config.get("Cell", "emodel"),
        "apical_point_isec": config.getint("Protocol", "apical_point_isec"),
        "mtype": config.get("Morphology", "mtype"),
        "prot_path": config.get("Paths", "prot_path"),
        "features_path": config.get("Paths", "features_path"),
    }


def get_syn_mech_args(config):
    """Get the dict containing synapse config used when loading synapse mechanisms."""
    return {
        "seed": config.getint("Synapses", "seed"),
        "rng_settings_mode": config.get("Synapses", "rng_settings_mode"),
        "syn_conf_file": config.get("Paths", "syn_conf_file"),
        "syn_data_file": config.get("Paths", "syn_data_file"),
        "syn_dir": config.get("Paths", "syn_dir"),
    }


def get_sscx_morph_args(config):
    """Get morphology arguments for SSCX from the configuration object.

    Args:
        config (configparser.ConfigParser): configuration object.

    Returns:
        dict: dictionary containing morphology arguments.
    """
    morph_path = config.get("Paths", "morph_path")
    # load axon hoc path
    axon_hoc_path = config.get("Paths", "replace_axon_hoc_path")
    return {
        "morph_path": morph_path,
        "axon_hoc_path": axon_hoc_path,
        "do_replace_axon": config.getboolean("Morphology", "do_replace_axon"),
    }


def get_synplas_morph_args(config, precell=False):
    """Get morphology arguments for Synplas from the configuration object.

    Args:
        config (dict): data from config file.
        precell (bool): True to load precell morph. False to load usual morph.

    Returns:
        dict: dictionary containing morphology arguments.
    """
    # load morphology path
    if precell:
        morph_path = config.get("Paths", "precell_morph_path")
    else:
        morph_path = config.get("Paths", "morph_path")

    return {
        "morph_path": morph_path,
        "do_replace_axon": config.getboolean("Morphology", "do_replace_axon"),
    }


def get_presyn_stim_args(config, pre_spike_train):
    """Get the dict containing pre-synaptic stimulus config."""
    # spikedelay is the time between the start of the stimulus
    # and the precell spike time
    spike_delay = config.getfloat("Protocol", "precell_spikedelay")

    # stim train is the times at which to stimulate the precell
    return {
        "stim_train": pre_spike_train - spike_delay,
        "amp": config.getfloat("Protocol", "precell_amplitude"),
        "width": config.getfloat("Protocol", "precell_width"),
    }


def load_emodel_params(emodel, params_path):
    """Get optimised parameters."""
    with open(params_path, "r", encoding="utf-8") as params_file:
        params = json.load(params_file)

    param_dict = params[emodel]["params"]

    return param_dict


def get_syn_setup_params(
    syn_dir,
    syn_extra_params_fname,
    cpre_cpost_fname,
    fit_params_path,
    gid,
    invivo,
):
    """Load json files and return syn_setup_params dict."""
    with open(
        os.path.join(syn_dir, syn_extra_params_fname), "r", encoding="utf-8"
    ) as f:
        syn_extra_params = json.load(f)
    with open(os.path.join(syn_dir, cpre_cpost_fname), "r", encoding="utf-8") as f:
        cpre_cpost = json.load(f)
    with open(fit_params_path, "r", encoding="utf-8") as f:
        fit_params = json.load(f)

    return {
        "syn_extra_params": syn_extra_params,
        "c_pre": cpre_cpost["c_pre"],
        "c_post": cpre_cpost["c_post"],
        "fit_params": fit_params,
        "postgid": gid,
        "invivo": invivo,
    }


def get_release_params(config, precell=False):
    """Return the final parameters."""
    if precell:
        emodel = config.get("Cell", "precell_emodel")
    else:
        emodel = config.get("Cell", "emodel")
    params_path = config.get("Paths", "params_path")

    release_params = load_emodel_params(params_path=params_path, emodel=emodel)

    return release_params


def load_mechanisms(mechs_path):
    """Define mechanisms."""
    with open(mechs_path, "r", encoding="utf-8") as mechs_file:
        mechs = json.load(mechs_file)
    mech_definitions = mechs["mechanisms"]

    mechanisms_list = []
    for sectionlist, channels in mech_definitions.items():

        seclist_locs = multi_locations(sectionlist)

        for channel in channels["mech"]:
            mechanisms_list.append(
                ephys.mechanisms.NrnMODMechanism(
                    name=f"{channel}.{sectionlist}",
                    mod_path=None,
                    suffix=channel,
                    locations=seclist_locs,
                    preloaded=True,
                )
            )

    return mechanisms_list


def load_unoptimized_parameters(params_path, v_init, celsius):
    """Load unoptimized parameters as BluePyOpt parameters.

    Args:
        params_path (str): path to the json file containing
            the non-optimised parameters
        v_init (float): initial voltage. Will override v_init value from parameter file
        celsius (float): cell temperature in celsius.
            Will override celsius value from parameter file
    """
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    parameters = []

    with open(params_path, "r", encoding="utf-8") as params_file:
        definitions = json.load(params_file)

    # set distributions
    distributions = collections.OrderedDict()
    distributions["uniform"] = ephys.parameterscalers.NrnSegmentLinearScaler()

    distributions_definitions = definitions["distributions"]
    for distribution, definition in distributions_definitions.items():

        if "parameters" in definition:
            dist_param_names = definition["parameters"]
        else:
            dist_param_names = None
        distributions[
            distribution
        ] = ephys.parameterscalers.NrnSegmentSomaDistanceScaler(
            name=distribution,
            distribution=definition["fun"],
            dist_param_names=dist_param_names,
        )

    params_definitions = definitions["parameters"]

    if "__comment" in params_definitions:
        del params_definitions["__comment"]

    for sectionlist, params in params_definitions.items():
        if sectionlist == "global":
            seclist_locs = None
            is_global = True
            is_dist = False
        elif "distribution_" in sectionlist:
            is_dist = True
            seclist_locs = None
            is_global = False
            dist_name = sectionlist.split("distribution_")[1]
            dist = distributions[dist_name]
        else:
            seclist_locs = multi_locations(sectionlist)
            is_global = False
            is_dist = False

        bounds = None
        value = None
        for param_config in params:
            param_name = param_config["name"]

            if isinstance(param_config["val"], (list, tuple)):
                is_frozen = False
                bounds = param_config["val"]
                value = None

            else:
                is_frozen = True
                value = param_config["val"]
                bounds = None

            if is_global:
                # force v_init to the given value
                if param_name == "v_init":
                    value = v_init
                elif param_name == "celsius":
                    value = celsius
                parameters.append(
                    ephys.parameters.NrnGlobalParameter(
                        name=param_name,
                        param_name=param_name,
                        frozen=is_frozen,
                        bounds=bounds,
                        value=value,
                    )
                )
            elif is_dist:
                parameters.append(
                    ephys.parameters.MetaParameter(
                        name=f"{param_name}.{sectionlist}",
                        obj=dist,
                        attr_name=param_name,
                        frozen=is_frozen,
                        bounds=bounds,
                        value=value,
                    )
                )

            else:
                if "dist" in param_config:
                    dist = distributions[param_config["dist"]]
                    use_range = True
                else:
                    dist = distributions["uniform"]
                    use_range = False

                if use_range:
                    parameters.append(
                        ephys.parameters.NrnRangeParameter(
                            name=f"{param_name}.{sectionlist}",
                            param_name=param_name,
                            value_scaler=dist,
                            value=value,
                            bounds=bounds,
                            frozen=is_frozen,
                            locations=seclist_locs,
                        )
                    )
                else:
                    parameters.append(
                        ephys.parameters.NrnSectionParameter(
                            name=f"{param_name}.{sectionlist}",
                            param_name=param_name,
                            value_scaler=dist,
                            value=value,
                            bounds=bounds,
                            frozen=is_frozen,
                            locations=seclist_locs,
                        )
                    )

    return parameters


def load_syn_mechs(
    seed,
    rng_settings_mode,
    syn_data_path,
    syn_conf_path,
    pre_mtypes=None,
    stim_params=None,
    use_glu_synapse=False,
    syn_setup_params=None,
):
    """Load synapse mechanisms."""
    # load synapse file data
    synapses_data = load_synapses_tsv_data(syn_data_path)

    # load synapse configuration
    synconf_dict = load_synapse_configuration_data(syn_conf_path)

    return NrnMODPointProcessMechanismCustom(
        "synapse_mechs",
        synapses_data,
        synconf_dict,
        seed,
        rng_settings_mode,
        pre_mtypes,
        stim_params,
        use_glu_synapse=use_glu_synapse,
        syn_setup_params=syn_setup_params,
    )


def load_synapses_tsv_data(tsv_path):
    """Load synapse data from tsv."""
    synapses = []
    with open(tsv_path, "r", encoding="utf-8") as f:
        # first line is dimensions
        for line in f.readlines()[1:]:
            syn = {}
            items = line.strip().split("\t")
            syn["sid"] = int(items[0])
            syn["pre_cell_id"] = int(items[1])
            syn["sectionlist_id"] = int(items[2])
            syn["sectionlist_index"] = int(items[3])
            syn["seg_x"] = float(items[4])
            syn["synapse_type"] = int(items[5])
            syn["dep"] = float(items[6])
            syn["fac"] = float(items[7])
            syn["use"] = float(items[8])
            syn["tau_d"] = float(items[9])
            syn["delay"] = float(items[10])
            syn["weight"] = float(items[11])
            syn["Nrrp"] = float(items[12])
            syn["pre_mtype"] = int(items[13])

            synapses.append(syn)

    return synapses


def load_synapse_configuration_data(synconf_path):
    """Load synapse configuration data into dict[command]=list(ids)."""
    synconf_dict = {}
    with open(synconf_path, "r", encoding="utf-8") as f:
        synconfs = f.read().split("-1000000000000000.0")

    for synconf in synconfs:
        tmp = synconf.split("\n")
        if "" in tmp:
            tmp.remove("")
        if len(tmp) == 2:
            cmd, ids = tmp
            ids = ids.replace(") ", ");")
            ids = ids.split(";")
            if "" in ids:
                ids.remove("")
            synconf_dict[cmd] = ids

    return synconf_dict
