"""Functions to create cells."""

import os

from emodelrunner.cell import CellModelCustom
from emodelrunner.load import (
    find_param_file,
    load_mechanisms,
    load_syn_mechs,
    define_parameters,
    load_params,
    load_constants,
    get_morph_args,
    get_syn_mech_args,
)
from emodelrunner.morphology import NrnFileMorphologyCustom, get_axon_hoc


def create_cell(
    recipes_path,
    emodel,
    add_synapses,
    syn_mech_args,
    morph_args,
    gid,
):
    """Create a cell."""
    # load mechanisms
    params_filepath = find_param_file(recipes_path, emodel)
    mechs = load_mechanisms(params_filepath)

    # add synapses mechs
    if add_synapses:
        mechs += [
            load_syn_mechs(
                syn_mech_args["seed"],
                syn_mech_args["rng_settings_mode"],
                os.path.join(syn_mech_args["syn_dir"], syn_mech_args["syn_data_file"]),
                os.path.join(syn_mech_args["syn_dir"], syn_mech_args["syn_conf_file"]),
            )
        ]

    # load parameters
    params = define_parameters(params_filepath)

    # load morphology
    replace_axon_hoc = get_axon_hoc(morph_args["axon_hoc_path"])
    morph = NrnFileMorphologyCustom(
        morph_args["morph_path"],
        do_replace_axon=morph_args["do_replace_axon"],
        replace_axon_hoc=replace_axon_hoc,
    )

    # create cell
    cell = CellModelCustom(
        name=emodel,
        morph=morph,
        mechs=mechs,
        params=params,
        gid=gid,
        add_synapses=add_synapses,
    )

    return cell


def create_cell_using_config(config):
    """Create a cell given configuration. Return cell, release params and time step."""
    # load constants
    constants_path = os.path.join(
        config.get("Paths", "constants_dir"), config.get("Paths", "constants_file")
    )
    emodel, morph_dir, morph_fname, dt_tmp, gid = load_constants(constants_path)

    # get recipes path
    recipes_path = "/".join(
        (config.get("Paths", "recipes_dir"), config.get("Paths", "recipes_file"))
    )

    # get synapse config data
    add_synapses = config.getboolean("Synapses", "add_synapses")
    syn_mech_args = get_syn_mech_args(config)

    # get morphology config data
    morph_args = get_morph_args(config, morph_fname, morph_dir)

    # load release params
    params_path = "/".join(
        (config.get("Paths", "params_dir"), config.get("Paths", "params_file"))
    )
    release_params = load_params(params_path=params_path, emodel=emodel)

    # create cell
    cell = create_cell(
        recipes_path,
        emodel,
        add_synapses,
        syn_mech_args,
        morph_args,
        gid,
    )

    return cell, release_params, dt_tmp
