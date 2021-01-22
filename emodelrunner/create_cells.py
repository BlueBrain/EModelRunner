"""Functions to create cells."""

import os

from emodelrunner.cell import CellModelCustom
from emodelrunner.load import (
    load_constants,
    find_param_file,
    load_mechanisms,
    load_syn_mechs,
    load_params,
    define_parameters,
    load_morphology,
)


def create_cell(config):
    """Create a cell. Returns cell, release params and time step."""
    # pylint: disable=too-many-locals
    # load constants
    constants_path = os.path.join(
        config.get("Paths", "constants_dir"), config.get("Paths", "constants_file")
    )
    emodel, morph_dir, morph_fname, dt_tmp, gid = load_constants(constants_path)

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
    params_path = "/".join(
        (config.get("Paths", "params_dir"), config.get("Paths", "params_file"))
    )
    release_params = load_params(params_path=params_path, emodel=emodel)
    params = define_parameters(params_filepath)

    # load morphology
    morph = load_morphology(config, morph_dir, morph_fname)

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
