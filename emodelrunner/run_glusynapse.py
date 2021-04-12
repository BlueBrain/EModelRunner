"""Run function to reproduce cells using glusynapses."""
import json
import logging
import os
import re

import h5py
import numpy as np

import bluepyopt.ephys as ephys
from emodelrunner.create_cells import create_cell
from emodelrunner.load import get_morph_args
from emodelrunner.load import get_release_params
from emodelrunner.load import get_syn_mech_args
from emodelrunner.load import get_syn_setup_params
from emodelrunner.load import load_config
from emodelrunner.protocols import define_glusynapse_protocols

# Configure logger
logger = logging.getLogger(__name__)


def write_output(
    responses,
    pre_spike_train,
    output_dir="",
    output_file="output.h5",
    syn_dir="synapses",
    syn_fname="synapse_properties.json",
):
    """Write output as h5."""
    results = {"prespikes": pre_spike_train}
    # add synprop
    synprop_path = os.path.join(syn_dir, syn_fname)
    if os.path.isfile(synprop_path):
        with open(synprop_path, "r") as f:
            synprop = json.load(f)
            results["synprop"] = synprop

    # add responses
    for key, resp in responses.items():
        if isinstance(resp, list):
            results[key] = np.transpose([np.array(rec["voltage"]) for rec in resp])
        else:
            results["t"] = np.array(resp["time"])
            results["v"] = np.array(resp["voltage"])

    # Store results
    output_path = os.path.join(output_dir, output_file)
    h5file = h5py.File(output_path, "w")
    for key in results:
        if key == "synprop":
            h5file.attrs.update(results["synprop"])
        else:
            h5file.create_dataset(
                key,
                data=results[key],
                chunks=True,
                compression="gzip",
                compression_opts=9,
            )
    h5file.close()


def get_cell(
    emodel,
    morph_fname,
    morph_dir,
    gid,
    fixhp=False,
    syn_setup_params=None,
    base_seed=0,
    v_init=-65,
):
    """Return a cell using glusynapse."""
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
        syn_mech_args,
        morph_args,
        gid,
        use_glu_synapse=True,
        fixhp=fixhp,
        syn_setup_params=syn_setup_params,
        v_init=v_init,
    )
    return cell


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
    cell = get_cell(
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
    protocol = define_glusynapse_protocols(
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
    write_output(responses, pre_spike_train)

    logger.info("Python Recordings Done.")


if __name__ == "__main__":
    run()
