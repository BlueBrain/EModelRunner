"""Functions mainly for loading params for run.py."""

import collections

try:
    import ConfigParser as configparser  # for python2
except ImportError:
    import configparser  # for python3
import json
import os

import bluepyopt.ephys as ephys

from emodelrunner.json_loader import json_load
from emodelrunner.synapse import NrnMODPointProcessMechanismCustom
from emodelrunner.morphology import NrnFileMorphologyCustom
from emodelrunner.locations import multi_locations


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
        config.read(config_path)

    # make sure that config has all sections
    secs = ["Cell", "Protocol", "Morphology", "Sim", "Synapses", "Paths"]
    for sec in secs:
        if not config.has_section(sec):
            config.add_section(sec)

    return config


def load_amps(config):
    """Load stimuli amplitudes from file."""
    amp_filename = os.path.join(
        config.get("Paths", "protocol_amplitudes_dir"),
        config.get("Paths", "protocol_amplitudes_file"),
    )
    with open(amp_filename, "r") as f:
        data = json.load(f)

    return data["amps"], data["holding"]


def get_axon_hoc(replace_axon_hoc):
    """Returns string containing replace axon hoc."""
    with open(replace_axon_hoc, "r") as f:
        return f.read()


def load_morphology(config, morph_dir, morph_fname):
    """Create the morphology."""
    # load morphology path
    if config.has_option("Paths", "morph_dir"):
        morph_dir = config.get("Paths", "morph_dir")
    else:
        morph_dir = os.path.join(config.get("Paths", "memodel_dir"), morph_dir)
    if config.has_option("Paths", "morph_file"):
        morph_fname = config.get("Paths", "morph_file")

    morph_path = os.path.join(morph_dir, morph_fname)

    # create morphology
    axon_hoc_path = os.path.join(
        config.get("Paths", "replace_axon_hoc_dir"),
        config.get("Paths", "replace_axon_hoc_file"),
    )
    replace_axon_hoc = get_axon_hoc(axon_hoc_path)
    do_replace_axon = config.getboolean("Morphology", "do_replace_axon")
    return NrnFileMorphologyCustom(
        morph_path,
        do_replace_axon=do_replace_axon,
        replace_axon_hoc=replace_axon_hoc,
    )


def find_param_file(recipes_path, emodel):
    """Find the parameter file for unfrozen params."""
    recipes = json_load(recipes_path)
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


def load_params(emodel, params_path):
    """Get optimised parameters."""
    params_file = json_load(params_path)
    data = params_file[emodel]

    param_dict = data["params"]

    return param_dict


def load_mechanisms(mechs_filepath):
    """Define mechanisms."""
    mech_definitions = json_load(mechs_filepath)["mechanisms"]

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


def define_parameters(params_filepath):
    """Define parameters."""
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    parameters = []

    definitions = json_load(params_filepath)

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


def load_syn_mechs(config, pre_mtypes=None, stim_params=None):
    """Load synapse mechanisms."""
    seed = config.getint("Synapses", "seed")
    rng_settings_mode = config.get("Synapses", "rng_settings_mode")
    syn_data_path = os.path.join(
        config.get("Paths", "syn_dir"), config.get("Paths", "syn_data_file")
    )
    syn_conf_path = os.path.join(
        config.get("Paths", "syn_dir"), config.get("Paths", "syn_conf_file")
    )

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
