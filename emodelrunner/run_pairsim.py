"""Run pair simulation for synapse plasticity simulation."""
import json
import logging
import os

import numpy as np
import bluepyopt.ephys as ephys
from emodelrunner.create_cells import get_precell, get_postcell
from emodelrunner.create_protocols import define_pairsim_protocols
from emodelrunner.load import get_presyn_stim_args
from emodelrunner.load import get_release_params
from emodelrunner.load import get_syn_setup_params
from emodelrunner.load import load_config
from emodelrunner.output import write_synplas_output
from emodelrunner.output import write_synplas_precell_output
from emodelrunner.run_synplas import _set_global_params

# Configure logger
logger = logging.getLogger(__name__)


def run(
    cvode_active=True,
    postsyn_protocol_name="pulse",
    presyn_protocol_name="presyn_pulse",
    fixhp=True,
    config_file="config_pairsim.ini",
):
    """Run cell with pulse stimuli and pre-cell spike train."""
    # pylint:disable=too-many-locals
    config = load_config(filename=config_file)

    constants_postcell_path = os.path.join("config", "constants.json")
    with open(constants_postcell_path, "r") as f:
        constants_postcell = json.load(f)

    constants_precell_path = os.path.join("config", "constants_precell.json")
    with open(constants_precell_path, "r") as f:
        constants_precell = json.load(f)

    # load extra_params
    syn_setup_params = get_syn_setup_params(
        "synapses", "syn_extra_params.json", "cpre_cpost.json", constants_postcell
    )

    # load cell
    postcell = get_postcell(
        emodel=constants_postcell["emodel"],
        morph_fname=constants_postcell["morph_fname"],
        morph_dir="morphology",
        gid=constants_postcell["gid"],
        fixhp=fixhp,
        syn_setup_params=syn_setup_params,
        base_seed=constants_postcell["base_seed"],
        v_init=constants_postcell["v_init"],
    )

    # load cell
    precell = get_precell(
        emodel=constants_precell["emodel"],
        morph_fname=constants_precell["morph_fname"],
        morph_dir="morphology",
        gid=constants_precell["gid"],
        fixhp=fixhp,
        v_init=constants_precell["v_init"],
    )

    sim = ephys.simulators.NrnSimulator(
        dt=constants_postcell["dt"], cvode_active=cvode_active
    )
    pre_release_params = get_release_params(constants_precell["emodel"])
    post_release_params = get_release_params(constants_postcell["emodel"])

    # set dynamic timestep tolerance
    sim.neuron.h.cvode.atolscale("v", 0.1)  # 0.01 for more precision

    # load spike_train
    spike_train_path = os.path.join("protocols", "out.dat")
    pre_spike_train = np.unique(np.loadtxt(spike_train_path, skiprows=1)[:, 0])

    # get pre-synaptic stimulus parameters
    presyn_stim_args = get_presyn_stim_args(config, pre_spike_train)

    # Set fitted model parameters
    if constants_postcell["fit_params"] is not None:
        _set_global_params(constants_postcell["fit_params"], sim)

    # Enable in vivo mode (global)
    if constants_postcell["invivo"]:
        sim.neuron.h.cao_CR_GluSynapse = 1.2  # mM

    # protocols
    protocol = define_pairsim_protocols(
        postcell,
        presyn_protocol_name,
        postsyn_protocol_name,
        cvode_active,
        constants_postcell["synrec"],
        constants_postcell["tstop"],
        constants_postcell["fastforward"],
        presyn_stim_args,
    )

    # run
    logger.info("Python Recordings Running...")

    responses = protocol.run(
        precell_model=precell,
        postcell_model=postcell,
        pre_param_values=pre_release_params,
        post_param_values=post_release_params,
        sim=sim,
    )

    # write responses
    write_synplas_output(responses[1], pre_spike_train)
    write_synplas_precell_output(responses[0], presyn_protocol_name)

    logger.info("Python Recordings Done.")


if __name__ == "__main__":
    run()
