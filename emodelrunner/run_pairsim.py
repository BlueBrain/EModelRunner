"""Run pair simulation for synapse plasticity simulation."""

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

import numpy as np
from bluepyopt import ephys
from emodelrunner.create_cells import get_precell, get_postcell
from emodelrunner.create_protocols import define_pairsim_protocols
from emodelrunner.load import get_presyn_stim_args
from emodelrunner.load import get_release_params
from emodelrunner.load import get_syn_setup_params
from emodelrunner.load import load_synplas_config
from emodelrunner.output import write_synplas_output
from emodelrunner.output import write_synplas_precell_output
from emodelrunner.run_synplas import _set_global_params

# Configure logger
logger = logging.getLogger(__name__)


def run(
    config_path,
    cvode_active=True,
    postsyn_protocol_name="pulse",
    presyn_protocol_name="presyn_pulse",
    fixhp=True,
):
    """Run cell with pulse stimuli and pre-cell spike train.

    Args:
        config_path (str): path to config file
        cvode_active (bool): whether to use variable time step
        postsyn_protocol_name (str): name of the postsynaptic protocol
        presyn_protocol_name (str): name of the presynaptic protocol
        fixhp (bool): to uninsert SK_E2 for hyperpolarization in cell model
    """
    # pylint:disable=too-many-locals
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

    sim = ephys.simulators.NrnSimulator(cvode_active=cvode_active)
    pre_release_params = get_release_params(config, precell=True)
    post_release_params = get_release_params(config)

    # set dynamic timestep tolerance
    sim.neuron.h.cvode.atolscale("v", 0.1)  # 0.01 for more precision

    # load spike_train
    spike_train_path = config.get("Paths", "spiketrain_path")
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
        config.get("Paths", "stimuli_path"),
    )

    # run
    logger.info("Python Recordings Running...")

    responses = protocol.run(
        precell_model=precell,
        postcell_model=postcell,
        pre_param_values=pre_release_params,
        post_param_values=post_release_params,
        sim=sim,
        isolate=False,
    )

    # write responses
    output_path = config.get("Paths", "pairsim_output_path")
    precell_output_path = config.get("Paths", "pairsim_precell_output_path")
    syn_prop_path = config.get("Paths", "syn_prop_path")
    write_synplas_output(responses[1], pre_spike_train, output_path, syn_prop_path)
    write_synplas_precell_output(
        responses[0], presyn_protocol_name, precell_output_path
    )

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
