"""Functions mainly for loading params for run.py."""

import collections

try:
    import ConfigParser as configparser  # for python2
except ImportError:
    import configparser  # for python3
import json
import os

import bluepyopt.ephys as ephys

from emodelrunner.json_utilities import load_package_json
from emodelrunner.synapses.mechanism import NrnMODPointProcessMechanismCustom
from emodelrunner.locations import multi_locations

# FileNotFoundError does not exist in python2.7
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError  # pylint: disable=redefined-builtin


def load_config(config_dir="config", filename=None):
    """Set config from config file and set default value."""
    defaults = {
        # protocol
        "step_stimulus": "True",
        "run_all_steps": "True",
        "run_step_number": "1",
        "total_duration": "3000",
        "stimulus_delay": "700",
        "stimulus_duration": "2000",
        "hold_stimulus_delay": "0",
        "hold_stimulus_duration": "3000",
        "syn_stim_mode": "vecstim",
        "syn_stop": "%(total_duration)s",
        "syn_interval": "100",
        "syn_nmb_of_spikes": "5",
        "syn_start": "50",
        "syn_noise": "0",
        "syn_stim_seed": "1",
        "vecstim_random": "python",  # can be "python" or "neuron"
        "precell_amplitude": "1.0",
        # morphology
        "do_replace_axon": "True",
        # sim
        "cvode_active": "False",
        # synapse
        "add_synapses": "False",
        "seed": "846515",
        "rng_settings_mode": "Random123",  # can be "Random123" or "Compatibility"
        # paths
        "memodel_dir": ".",
        "output_dir": "%(memodel_dir)s/python_recordings",
        "output_file": "soma_voltage_",
        "constants_dir": "config",
        "constants_file": "constants.json",
        "recipes_dir": "config/recipes",
        "recipes_file": "recipes.json",
        "params_dir": "config/params",
        "params_file": "final.json",
        "protocol_amplitudes_dir": "config",
        "protocol_amplitudes_file": "current_amps.json",
        "templates_dir": "templates",
        "hoc_file": "cell.hoc",
        "create_hoc_template_file": "cell_template_neurodamus.jinja2",
        "replace_axon_hoc_dir": "%(templates_dir)s",
        "replace_axon_hoc_file": "replace_axon_hoc.hoc",
        "syn_dir_for_hoc": "synapses",
        "syn_dir": "%(memodel_dir)s/%(syn_dir_for_hoc)s",
        "syn_data_file": "synapses.tsv",
        "syn_conf_file": "synconf.txt",
        "syn_hoc_file": "synapses.hoc",
        "syn_mtype_map": "mtype_map.tsv",
        "simul_hoc_file": "createsimulation.hoc",
    }

    config = configparser.ConfigParser(defaults=defaults)
    if filename is not None:
        config_path = os.path.join(config_dir, filename)
        if not os.path.exists(config_path):
            raise FileNotFoundError("The file at {} does not exist".format(config_path))

        config.read(config_path)

    # make sure that config has all sections
    secs = ["Cell", "Protocol", "Morphology", "Sim", "Synapses", "Paths"]
    for sec in secs:
        if not config.has_section(sec):
            config.add_section(sec)

    return config


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


def get_step_prot_args(config):
    """Get the dict containing step & holding protocols configuration data."""
    return {
        "total_duration": config.getint("Protocol", "total_duration"),
        "step_delay": config.getint("Protocol", "stimulus_delay"),
        "step_duration": config.getint("Protocol", "stimulus_duration"),
        "hold_step_delay": config.getint("Protocol", "hold_stimulus_delay"),
        "hold_step_duration": config.getint("Protocol", "hold_stimulus_duration"),
        "run_all_steps": config.getboolean("Protocol", "run_all_steps"),
        "run_step_number": config.getint("Protocol", "run_step_number"),
    }


def get_syn_prot_args(config):
    """Get the dict containing synapse protocols configuration data."""
    return {
        "netstim_total_duration": config.getint("Protocol", "total_duration"),
        "syn_stop": config.getint("Protocol", "syn_stop"),
        "syn_interval": config.getint("Protocol", "syn_interval"),
        "syn_nmb_of_spikes": config.getint("Protocol", "syn_nmb_of_spikes"),
        "syn_start": config.getint("Protocol", "syn_start"),
        "syn_noise": config.getint("Protocol", "syn_noise"),
        "syn_stim_seed": config.getint("Protocol", "syn_stim_seed"),
        "vecstim_random": config.get("Protocol", "vecstim_random"),
        "syn_stim_mode": config.get("Protocol", "syn_stim_mode"),
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


def get_morph_args(config, morph_fname, morph_dir):
    """Get the dict containing morphology configuration data.

    Args:
        config (dict): data from config file.
        morph_fname (str): morphology file name according to constants file.
        morph_dir (str): path to repo containing the morphology according to constants.
    """
    # load morphology path
    if config.has_option("Paths", "morph_dir"):
        morph_dir = config.get("Paths", "morph_dir")
    else:
        morph_dir = os.path.join(config.get("Paths", "memodel_dir"), morph_dir)
    if config.has_option("Paths", "morph_file"):
        morph_fname = config.get("Paths", "morph_file")

    morph_path = os.path.join(morph_dir, morph_fname)

    # load axon hoc path
    axon_hoc_path = os.path.join(
        config.get("Paths", "replace_axon_hoc_dir"),
        config.get("Paths", "replace_axon_hoc_file"),
    )
    return {
        "morph_path": morph_path,
        "axon_hoc_path": axon_hoc_path,
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
        "width": config.getint("Protocol", "precell_width"),
    }


def load_amps(amps_path):
    """Load stimuli amplitudes from file."""
    with open(amps_path, "r") as f:
        data = json.load(f)

    return data["amps"], data["holding"]


def find_param_file(recipes_path, emodel):
    """Find the parameter file for unfrozen params."""
    recipes = load_package_json(recipes_path)
    recipe = recipes[emodel]

    return recipe["params"]


def load_constants(constants_path):
    """Get etype, morphology, timestep and gid."""
    with open(constants_path, "r") as f:
        data = json.load(f)

    emodel = data["template_name"]
    morph_dir = data["morph_dir"]
    morph_fname = data["morph_fname"]
    dt = data["dt"]
    gid = data["gid"]

    return emodel, morph_dir, morph_fname, dt, gid


def load_emodel_params(emodel, params_path):
    """Get optimised parameters."""
    params_file = load_package_json(params_path)
    data = params_file[emodel]

    param_dict = data["params"]

    return param_dict


def get_syn_setup_params(syn_dir, syn_extra_params_fname, cpre_cpost_fname, constants):
    """Load json files and return syn_setup_params dict."""
    with open(os.path.join(syn_dir, syn_extra_params_fname), "r") as f:
        syn_extra_params = json.load(f)
    with open(os.path.join(syn_dir, cpre_cpost_fname), "r") as f:
        cpre_cpost = json.load(f)

    return {
        "syn_extra_params": syn_extra_params,
        "c_pre": cpre_cpost["c_pre"],
        "c_post": cpre_cpost["c_post"],
        "fit_params": constants["fit_params"],
        "postgid": constants["gid"],
        "invivo": constants["invivo"],
    }


def get_release_params(emodel):
    """Return the final parameters."""
    config = load_config()

    params_path = "/".join(
        (config.get("Paths", "params_dir"), config.get("Paths", "params_file"))
    )
    release_params = load_emodel_params(params_path=params_path, emodel=emodel)

    return release_params


def load_mechanisms(mechs_filepath):
    """Define mechanisms."""
    mech_definitions = load_package_json(mechs_filepath)["mechanisms"]

    mechanisms_list = []
    for sectionlist, channels in mech_definitions.items():

        seclist_locs = multi_locations(sectionlist)

        for channel in channels["mech"]:
            mechanisms_list.append(
                ephys.mechanisms.NrnMODMechanism(
                    name="%s.%s" % (channel, sectionlist),
                    mod_path=None,
                    suffix=channel,
                    locations=seclist_locs,
                    preloaded=True,
                )
            )

    return mechanisms_list


def define_parameters(params_filepath, v_init=None):
    """Define parameters."""
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    parameters = []

    definitions = load_package_json(params_filepath)

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
                if param_name == "v_init" and v_init is not None:
                    value = v_init
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
                        name="%s.%s" % (param_name, sectionlist),
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
                            name="%s.%s" % (param_name, sectionlist),
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
                            name="%s.%s" % (param_name, sectionlist),
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
    synapses_data = load_tsv_data(syn_data_path)

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


def load_tsv_data(tsv_path):
    """Load synapse data from tsv."""
    synapses = []
    with open(tsv_path, "r") as f:
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
    with open(synconf_path, "r") as f:
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
