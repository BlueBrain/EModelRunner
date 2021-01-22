"""Functions to create cells."""

import os

from emodelrunner.morphology import NrnFileMorphologyCustom
from emodelrunner.cell import CellModelCustom
from emodelrunner.load import (
    load_constants,
    find_param_file,
    load_mechanisms,
    load_syn_mechs,
    load_params,
    define_parameters,
)


def get_axon_hoc(replace_axon_hoc):
    """Returns string containing replace axon hoc."""
    with open(replace_axon_hoc, "r") as f:
        return f.read()


def create_cell(config):
    """Create a cell. Returns cell, release params and time step."""
    # load constants
    constants_path = os.path.join(
        config.get("Paths", "constants_dir"), config.get("Paths", "constants_file")
    )
    emodel, morph_dir, morph_fname, dt_tmp, gid = load_constants(constants_path)

    # load morphology path
    if config.has_option("Paths", "morph_dir"):
        morph_dir = config.get("Paths", "morph_dir")
    else:
        morph_dir = os.path.join(config.get("Paths", "memodel_dir"), morph_dir)
    if config.has_option("Paths", "morph_file"):
        morph_fname = config.get("Paths", "morph_file")

    morph_path = os.path.join(morph_dir, morph_fname)

    # load mechanisms
    recipes_path = "/".join(
        (config.get("Paths", "recipes_dir"), config.get("Paths", "recipes_file"))
    )
    params_filepath = find_param_file(recipes_path, emodel)
    mechs = load_mechanisms(params_filepath)

    # add synapses mechs
    add_synapses = config.getboolean("Synapses", "add_synapses")
    if add_synapses:
        mechs += [load_syn_mechs(config)]

    # load parameters
    params_path = "/".join((config.get("Paths", "params_dir"), config.get("Paths", "params_file")))
    release_params = load_params(params_path=params_path, emodel=emodel)
    params = define_parameters(params_filepath)

    # create morphology
    axon_hoc_path = os.path.join(
        config.get("Paths", "replace_axon_hoc_dir"),
        config.get("Paths", "replace_axon_hoc_file"),
    )
    replace_axon_hoc = get_axon_hoc(axon_hoc_path)
    do_replace_axon = config.getboolean("Morphology", "do_replace_axon")
    morph = NrnFileMorphologyCustom(
        morph_path,
        do_replace_axon=do_replace_axon,
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

    return cell, release_params, dt_tmp
