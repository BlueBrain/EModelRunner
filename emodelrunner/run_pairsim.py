"""Run pair simulation for synapse plasticity simulation."""
import argparse
import json
import logging
import os

import numpy as np
from bluepyopt import ephys
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

    # load extra_params
    syn_setup_params = get_syn_setup_params(
        "synapses",
        "syn_extra_params.json",
        "cpre_cpost.json",
        config.get("Paths", "synplas_fit_params_path"),
        config.getint("Cell", "gid"),
        config.getboolean("SynapsePlasticity", "invivo"),
    )

    # load cell
    postcell = get_postcell(
        config,
        fixhp=fixhp,
        syn_setup_params=syn_setup_params,
    )

    # load cell
    precell = get_precell(
        config,
        fixhp=fixhp,
    )

    sim = ephys.simulators.NrnSimulator(
        dt=config.getfloat("Sim", "dt"), cvode_active=cvode_active
    )
    pre_release_params = get_release_params(config, precell=True)
    post_release_params = get_release_params(config)

    # set dynamic timestep tolerance
    sim.neuron.h.cvode.atolscale("v", 0.1)  # 0.01 for more precision

    # load spike_train
    spike_train_path = os.path.join("protocols", "out.dat")
    pre_spike_train = np.unique(np.loadtxt(spike_train_path, skiprows=1)[:, 0])

    # get pre-synaptic stimulus parameters
    presyn_stim_args = get_presyn_stim_args(config, pre_spike_train)

    # Set fitted model parameters
    if syn_setup_params["fit_params"]:
        _set_global_params(syn_setup_params["fit_params"], sim)

    # Enable in vivo mode (global)
    if config.getboolean("SynapsePlasticity", "invivo"):
        sim.neuron.h.cao_CR_GluSynapse = 1.2  # mM

    # protocols
    protocol = define_pairsim_protocols(
        postcell,
        presyn_protocol_name,
        postsyn_protocol_name,
        cvode_active,
        json.loads(config.get("SynapsePlasticity", "synrec")),
        config.getfloat("Protocol", "tstop"),
        config.getfloat("SynapsePlasticity", "fastforward"),
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--c",
        default="config_pairsim.ini",
        help="the name of the config file",
    )
    args = parser.parse_args()

    _config_file = args.c
    run(config_file=_config_file)
