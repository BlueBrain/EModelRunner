"""Functions to create cells."""

import os

from emodelrunner.cell import CellModelCustom
from emodelrunner.load import (
    load_config,
    find_param_file,
    load_mechanisms,
    load_syn_mechs,
    define_parameters,
    load_constants,
    get_morph_args,
    get_syn_mech_args,
    get_release_params,
)
from emodelrunner.morphology import NrnFileMorphologyCustom, get_axon_hoc


def create_cell(
    recipes_path,
    emodel,
    add_synapses,
    morph_args,
    gid,
    syn_mech_args=None,
    use_glu_synapse=False,
    fixhp=False,
    syn_setup_params=None,
    v_init=None,
):
    """Create a cell."""
    # pylint: disable=too-many-arguments, too-many-locals
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
                use_glu_synapse=use_glu_synapse,
                syn_setup_params=syn_setup_params,
            )
        ]

    # load parameters
    params = define_parameters(params_filepath, v_init)

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
        fixhp=fixhp,
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
    release_params = get_release_params(emodel)

    # create cell
    cell = create_cell(
        recipes_path,
        emodel,
        add_synapses,
        morph_args,
        gid,
        syn_mech_args,
    )

    return cell, release_params, dt_tmp


def get_postcell(
    emodel,
    morph_fname,
    morph_dir,
    gid,
    fixhp=False,
    syn_setup_params=None,
    base_seed=0,
    v_init=-65,
):
    """Return the postcell for synapse plasticity run."""
    config = load_config()

    recipes_path = "/".join(
        (config.get("Paths", "recipes_dir"), config.get("Paths", "recipes_file"))
    )

    syn_mech_args = get_syn_mech_args(config)
    # rewrite seed and rng setting mode over basic emodelrunner config defaults
    syn_mech_args["seed"] = base_seed
    syn_mech_args["rng_settings_mode"] = "Compatibility"

    morph_args = get_morph_args(config, morph_fname, morph_dir)

    add_synapses = True

    cell = create_cell(
        recipes_path,
        emodel,
        add_synapses,
        morph_args,
        gid,
        syn_mech_args,
        use_glu_synapse=True,
        fixhp=fixhp,
        syn_setup_params=syn_setup_params,
        v_init=v_init,
    )
    return cell


def get_precell(
    emodel,
    morph_fname,
    morph_dir,
    gid,
    fixhp=False,
    v_init=-65,
):
    """Return the precell for synapse plasticity pair simulation run."""
    config = load_config()

    recipes_path = "/".join(
        (config.get("Paths", "recipes_dir"), config.get("Paths", "recipes_file"))
    )

    morph_args = get_morph_args(config, morph_fname, morph_dir)

    add_synapses = False

    cell = create_cell(
        recipes_path,
        emodel,
        add_synapses,
        morph_args,
        gid,
        fixhp=fixhp,
        v_init=v_init,
    )
    return cell
