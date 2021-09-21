"""Functions to create cells."""

import os

from emodelrunner.cell import CellModelCustom
from emodelrunner.load import (
    load_mechanisms,
    load_syn_mechs,
    load_unoptimized_parameters,
    get_morph_args,
    get_syn_mech_args,
)
from emodelrunner.morphology import NrnFileMorphologyCustom, get_axon_hoc


def create_cell(
    unopt_params_path,
    emodel,
    add_synapses,
    morph_args,
    gid,
    syn_mech_args=None,
    use_glu_synapse=False,
    fixhp=False,
    syn_setup_params=None,
    v_init=-80,
    celsius=34,
):
    """Create a cell."""
    # pylint: disable=too-many-arguments, too-many-locals
    # load mechanisms
    mechs = load_mechanisms(unopt_params_path)

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
    params = load_unoptimized_parameters(unopt_params_path, v_init, celsius)

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
    unopt_params_path = config.get("Paths", "unoptimized_params_path")

    # get synapse config data
    add_synapses = config.getboolean("Synapses", "add_synapses")
    syn_mech_args = get_syn_mech_args(config)

    # get morphology config data
    morph_args = get_morph_args(config)

    # create cell
    cell = create_cell(
        unopt_params_path,
        config.get("Cell", "emodel"),
        add_synapses,
        morph_args,
        config.getint("Cell", "gid"),
        syn_mech_args,
        v_init=config.getint("Cell", "v_init"),
        celsius=config.getint("Cell", "celsius"),
    )

    return cell


def get_postcell(
    config,
    fixhp=False,
    syn_setup_params=None,
):
    """Return the postcell for synapse plasticity run."""
    emodel = config.get("Cell", "emodel")
    gid = config.getint("Cell", "gid")
    base_seed = config.getint("SynapsePlasticity", "base_seed")
    v_init = config.getint("Cell", "v_init")
    celsius = config.getint("Cell", "celsius")

    unopt_params_path = config.get("Paths", "unoptimized_params_path")

    syn_mech_args = get_syn_mech_args(config)
    # rewrite seed and rng setting mode over basic emodelrunner config defaults
    syn_mech_args["seed"] = base_seed
    syn_mech_args["rng_settings_mode"] = "Compatibility"

    morph_args = get_morph_args(config)

    add_synapses = True

    cell = create_cell(
        unopt_params_path,
        emodel,
        add_synapses,
        morph_args,
        gid,
        syn_mech_args,
        use_glu_synapse=True,
        fixhp=fixhp,
        syn_setup_params=syn_setup_params,
        v_init=v_init,
        celsius=celsius,
    )
    return cell


def get_precell(
    config,
    fixhp=False,
):
    """Return the precell for synapse plasticity pair simulation run."""
    emodel = config.get("Cell", "emodel")
    gid = config.getint("Cell", "gid")
    v_init = config.getint("Cell", "v_init")
    celsius = config.getint("Cell", "celsius")

    unopt_params_path = config.get("Paths", "precell_unoptimized_params_path")

    morph_args = get_morph_args(config, precell=True)

    add_synapses = False

    cell = create_cell(
        unopt_params_path,
        emodel,
        add_synapses,
        morph_args,
        gid,
        fixhp=fixhp,
        v_init=v_init,
        celsius=celsius,
    )
    return cell
