"""Run function to for synapse plasticity simulation."""
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
):
    """Run cell with pulse stimuli and pre-cell spike train."""
    constants_path = os.path.join("config", "constants.json")
    with open(constants_path, "r") as f:
        constants = json.load(f)

    # load extra_params
    syn_setup_params = get_syn_setup_params(
        "synapses", "syn_extra_params.json", "cpre_cpost.json", constants
    )

    # load cell
    cell = get_postcell(
        emodel=constants["emodel"],
        morph_fname=constants["morph_fname"],
        morph_dir="morphology",
        gid=constants["gid"],
        fixhp=fixhp,
        syn_setup_params=syn_setup_params,
        base_seed=constants["base_seed"],
        v_init=constants["v_init"],
    )

    sim = ephys.simulators.NrnSimulator(dt=constants["dt"], cvode_active=cvode_active)
    release_params = get_release_params(constants["emodel"])

    # set dynamic timestep tolerance
    sim.neuron.h.cvode.atolscale("v", 0.1)  # 0.01 for more precision

    # get pre_spike_train
    spike_train_path = os.path.join("protocols", "out.dat")
    pre_spike_train = np.unique(np.loadtxt(spike_train_path, skiprows=1)[:, 0])

    # Set fitted model parameters
    if constants["fit_params"] is not None:
        _set_global_params(constants["fit_params"], sim)

    # Enable in vivo mode (global)
    if constants["invivo"]:
        sim.neuron.h.cao_CR_GluSynapse = 1.2  # mM

    # protocols
    protocol = define_synapse_plasticity_protocols(
        cell,
        pre_spike_train,
        protocol_name,
        cvode_active,
        constants["synrec"],
        constants["tstop"],
        constants["fastforward"],
    )

    # run
    logger.info("Python Recordings Running...")

    responses = protocol.run(cell_model=cell, param_values=release_params, sim=sim)

    # write responses
    write_synplas_output(responses, pre_spike_train)

    logger.info("Python Recordings Done.")


if __name__ == "__main__":
    run()
