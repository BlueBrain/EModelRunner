"""Functions mainly for loading params for run.py."""

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

import collections

import json

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
    """Get the dict containing the paths to the hoc files.

    Args:
        config (configparser.ConfigParser): configuration

    Returns:
        dict: hoc paths related configuration data
    """
    return {
        "hoc_dir": config.get("Paths", "memodel_dir"),
        "cell_hoc_filename": config.get("Paths", "cell_hoc_file"),
        "simul_hoc_filename": config.get("Paths", "simul_hoc_file"),
        "run_hoc_filename": config.get("Paths", "run_hoc_file"),
        "syn_dir": config.get("Paths", "syn_dir"),
        "syn_dir_for_hoc": config.get("Paths", "syn_dir_for_hoc"),
        "syn_hoc_filename": config.get("Paths", "syn_hoc_file"),
        "main_protocol_filename": config.get("Paths", "main_protocol_file"),
    }


def get_prot_args(config):
    """Get the dict containing protocols configuration data.

    Args:
        config (configparser.ConfigParser): configuration

    Returns:
        dict: protocol related configuration data
    """
    return {
        "emodel": config.get("Cell", "emodel"),
        "apical_point_isec": config.getint("Protocol", "apical_point_isec"),
        "mtype": config.get("Morphology", "mtype"),
        "prot_path": config.get("Paths", "prot_path"),
        "features_path": config.get("Paths", "features_path"),
    }


def get_syn_mech_args(config):
    """Get the dict containing synapse config used when loading synapse mechanisms.

    Args:
        config (configparser.ConfigParser): configuration

    Returns:
        dict: synapse related configuration data
    """
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
        config (configparser.ConfigParser): configuration
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
    """Get the dict containing pre-synaptic stimulus config.

    Args:
        config (configparser.ConfigParser): configuration
        pre_spike_train (list): times at which the synapses fire (ms)

    Returns:
        dict: presynaptic stimuli related configuration data
    """
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
    """Get optimized parameters.

    Args:
        emodel (str): name of the emodel
        params_path (str): path to the optimized parameters json file

    Returns:
        dict: optimized parameters for the given emodel
    """
    with open(params_path, "r", encoding="utf-8") as params_file:
        params = json.load(params_file)

    param_dict = params[emodel]["params"]

    return param_dict


def get_syn_setup_params(
    syn_extra_params_path,
    cpre_cpost_path,
    fit_params_path,
    gid,
    invivo,
):
    """Load json files and return syn_setup_params dict.

    Args:
        syn_extra_params_path (str): path to the glusynapses related extra parameters file
        cpre_cpost_path (str): path to the c_pre and c_post related file
            c_pre (resp. c_post) is the calcium amplitude during isolated presynaptic
            (resp. postsynaptic) activation
        fit_params_path (str): path to the file containing the glusynapse fitted parameters
            The fitted parameters are time constant of calcium integrator, depression rate,
            potentiation rate, and factors used in plasticity threshold computation.
        gid (int): ID of the postsynaptic cell
        invivo (bool): whether to run the simulation in 'in vivo' conditions

    Returns:
        dict: glusynapse setup related parameters
    """
    with open(syn_extra_params_path, "r", encoding="utf-8") as f:
        syn_extra_params = json.load(f)
    with open(cpre_cpost_path, "r", encoding="utf-8") as f:
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
    """Return the final parameters.

    Args:
        config (configparser.ConfigParser): configuration
        precell (bool): True to load precell optimized parameters. False to get usual parameters.

    Returns:
        dict: optimized parameters
    """
    if precell:
        emodel = config.get("Cell", "precell_emodel")
    else:
        emodel = config.get("Cell", "emodel")
    params_path = config.get("Paths", "params_path")

    release_params = load_emodel_params(params_path=params_path, emodel=emodel)

    return release_params


def load_mechanisms(mechs_path):
    """Define mechanisms.

    Args:
        mechs_path (str): path to the unoptimized parameters json file

    Returns:
        list of ephys.mechanisms.NrnMODMechanism from file
    """
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
        v_init (int): initial voltage (mV). Will override v_init value from parameter file
        celsius (int): cell temperature in celsius.
            Will override celsius value from parameter file

    Returns:
        list of parameters
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
    """Load synapse mechanisms.

    Args:
        seed (int): random number generator seed number
        rng_settings_mode (str): mode of the random number generator
            Can be "Random123" or "Compatibility"
        syn_data_path (str): path to the (tsv) synapses data file
        syn_conf_path (str): path to the synapse configuration data file
        pre_mtypes (list of ints): activate only synapses whose pre_mtype
            is in this list. if None, all synapses are activated
        stim_params (dict or None): dict with pre_mtype as key,
            and netstim params list as item.
            netstim params list is [start, interval, number, noise]
        use_glu_synapse (bool): if True, instantiate synapses to use GluSynapse
        syn_setup_params (dict): contains extra parameters to setup synapses
            when using GluSynapseCustom

    Returns:
        NrnMODPointProcessMechanismCustom: the synapses mechanisms
    """
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
    """Load synapse data from tsv.

    Args:
        tsv_path (str): path to the tsv synapses data file

    Returns:
        list of dicts containing each data for one synapse
    """
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
    """Load synapse configuration data into dict[command]=list(ids).

    Args:
        synconf_path (str): path to the synapse configuration data file

    Returns:
        dict: configuration data

        each key contains a command to execute using hoc,
        and each value contains a list of synapse id on which to execute the command
    """
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
