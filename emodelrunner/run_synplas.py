"""Run function to for synapse plasticity simulation."""

# Copyright 2020-2021 Blue Brain Project / EPFL

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import logging
import re

import numpy as np

from bluepyopt import ephys
from emodelrunner.create_cells import get_postcell
from emodelrunner.create_protocols import define_synapse_plasticity_protocols
from emodelrunner.load import get_release_params
from emodelrunner.load import get_syn_setup_params
from emodelrunner.load import load_synplas_config
from emodelrunner.output import write_synplas_output

# Configure logger
logger = logging.getLogger(__name__)


# taken from glusynapse.simulation.simulator
def _set_global_params(allparams, sim):
    """Set the global parameters of glusynapses.

    Args:
        allparams (dict): global glusynapse parameter to be set
        sim (bluepyopt.ephys.NrnSimulator): neuron simulator
    """
    logger.debug("Setting global parameters")
    for param_name, param_val in allparams.items():
        if re.match(".*_GluSynapse$", param_name):
            # Set parameter
            setattr(sim.neuron.h, param_name, param_val)
            logger.debug("\t%s = %f", param_name, getattr(sim.neuron.h, param_name))


def run(
    config_path,
    cvode_active=True,
    protocol_name="pulse",
    fixhp=True,
):
    """Run cell with pulse stimuli and pre-cell spike train.

    Args:
        config_path (str): path to config file
        cvode_active (bool): whether to use variable time step
        protocol_name (str): name of the protocol
        fixhp (bool): to uninsert SK_E2 for hyperpolarization in cell model
    """
    config = load_synplas_config(config_path=config_path)

    # load extra_params
    syn_setup_params = get_syn_setup_params(
        "synapses/syn_extra_params.json",
        "synapses/cpre_cpost.json",
        config.get("Paths", "synplas_fit_params_path"),
        config.getint("Cell", "gid"),
        config.getboolean("SynapsePlasticity", "invivo"),
    )

    # load cell
    cell = get_postcell(
        config=config,
        fixhp=fixhp,
        syn_setup_params=syn_setup_params,
    )

    sim = ephys.simulators.NrnSimulator(cvode_active=cvode_active)
    release_params = get_release_params(config)

    # set dynamic timestep tolerance
    sim.neuron.h.cvode.atolscale("v", 0.1)  # 0.01 for more precision

    # get pre_spike_train
    spike_train_path = config.get("Paths", "spiketrain_path")
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
        config.get("Paths", "stimuli_path"),
    )

    # run
    logger.info("Python Recordings Running...")

    responses = protocol.run(
        cell_model=cell, param_values=release_params, sim=sim, isolate=False
    )

    # write responses
    output_path = config.get("Paths", "synplas_output_path")
    syn_prop_path = config.get("Paths", "syn_prop_path")
    write_synplas_output(responses, pre_spike_train, output_path, syn_prop_path)

    logger.info("Python Recordings Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config_path",
        default=None,
        help="the path to the config file.",
    )
    args = parser.parse_args()

    run(config_path=args.config_path)
