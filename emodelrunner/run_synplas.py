"""Run function to for synapse plasticity simulation."""
import argparse
import json
import logging
import os
import re

import numpy as np

from bluepyopt import ephys
from emodelrunner.create_cells import get_postcell
from emodelrunner.create_protocols import define_synapse_plasticity_protocols
from emodelrunner.load import get_release_params
from emodelrunner.load import get_syn_setup_params
from emodelrunner.load import load_config
from emodelrunner.output import write_synplas_output

# Configure logger
logger = logging.getLogger(__name__)


# taken from glusynapse.simulation.simulator
def _set_global_params(allparams, sim):
    logger.debug("Setting global parameters")
    for param_name, param_val in allparams.items():
        if re.match(".*_GluSynapse$", param_name):
            # Set parameter
            setattr(sim.neuron.h, param_name, param_val)
            logger.debug("\t%s = %f", param_name, getattr(sim.neuron.h, param_name))


def run(
    cvode_active=True,
    protocol_name="pulse",
    fixhp=True,
    config_file="config_pairsim.ini",
):
    """Run cell with pulse stimuli and pre-cell spike train."""
    config = load_config(filename=config_file)

    # load extra_params
    syn_setup_params = get_syn_setup_params(
        "synapses",
        "syn_extra_params.json",
        "cpre_cpost.json",
        config.get("Paths", "synplas_fit_params_dir"),
        config.get("Paths", "synplas_fit_params_file"),
        config.getint("Cell", "gid"),
        config.getboolean("SynapsePlasticity", "invivo"),
    )

    # load cell
    cell = get_postcell(
        config=config,
        fixhp=fixhp,
        syn_setup_params=syn_setup_params,
    )

    sim = ephys.simulators.NrnSimulator(
        dt=config.getfloat("Sim", "dt"), cvode_active=cvode_active
    )
    release_params = get_release_params(config.get("Cell", "emodel"))

    # set dynamic timestep tolerance
    sim.neuron.h.cvode.atolscale("v", 0.1)  # 0.01 for more precision

    # get pre_spike_train
    spike_train_path = os.path.join("protocols", "out.dat")
    pre_spike_train = np.unique(np.loadtxt(spike_train_path, skiprows=1)[:, 0])

    # Set fitted model parameters
    if syn_setup_params["fit_params"]:
        _set_global_params(syn_setup_params["fit_params"], sim)

    # Enable in vivo mode (global)
    if config.getboolean("SynapsePlasticity", "invivo"):
        sim.neuron.h.cao_CR_GluSynapse = 1.2  # mM

    # protocols
    protocol = define_synapse_plasticity_protocols(
        cell,
        pre_spike_train,
        protocol_name,
        cvode_active,
        json.loads(config.get("SynapsePlasticity", "synrec")),
        config.getfloat("Protocol", "tstop"),
        config.getfloat("SynapsePlasticity", "fastforward"),
    )

    # run
    logger.info("Python Recordings Running...")

    responses = protocol.run(cell_model=cell, param_values=release_params, sim=sim)

    # write responses
    write_synplas_output(responses, pre_spike_train)

    logger.info("Python Recordings Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--c",
        default=None,
        help="the name of the config file",
    )
    args = parser.parse_args()

    _config_file = args.c
    if _config_file is None:
        run()
    else:
        run(config_file=_config_file)
