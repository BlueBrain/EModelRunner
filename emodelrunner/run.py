"""Create python recordings."""

import argparse
import os
import numpy as np

import bluepyopt.ephys as ephys

from emodelrunner.load import (
    load_config,
    get_step_prot_args,
    get_syn_prot_args,
)
from emodelrunner.protocols import define_protocols
from emodelrunner.create_cells import create_cell_using_config


def write_responses(responses, output_dir, output_file):
    """Write each response in a file."""
    for key, resp in responses.items():
        output_path = os.path.join(output_dir, output_file + key + ".dat")

        time = np.array(resp["time"])
        soma_voltage = np.array(resp["voltage"])

        np.savetxt(output_path, np.transpose(np.vstack((time, soma_voltage))))


def main(config_file):
    """Main."""
    # pylint: disable=too-many-locals
    config = load_config(filename=config_file)

    cell, release_params, dt_tmp = create_cell_using_config(config)

    cvode_active = config.getboolean("Sim", "cvode_active")

    # simulator
    if config.has_section("Sim") and config.has_option("Sim", "dt"):
        dt = config.getfloat("Sim", "dt")
    else:
        dt = dt_tmp
    sim = ephys.simulators.NrnSimulator(dt=dt, cvode_active=cvode_active)

    # create protocols
    step_stim = config.getboolean("Protocol", "step_stimulus")
    add_synapses = config.getboolean("Synapses", "add_synapses")
    step_args = get_step_prot_args(config)
    syn_args = get_syn_prot_args(config)
    amps_path = os.path.join(
        config.get("Paths", "protocol_amplitudes_dir"),
        config.get("Paths", "protocol_amplitudes_file"),
    )

    protocols = define_protocols(
        step_args, syn_args, step_stim, add_synapses, amps_path, cvode_active, cell
    )

    # run
    print("Python Recordings Running...")

    responses = protocols.run(cell_model=cell, param_values=release_params, sim=sim)

    # write responses
    output_dir = config.get("Paths", "output_dir")
    output_file = config.get("Paths", "output_file")
    write_responses(responses, output_dir, output_file)

    print("Python Recordings Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--c",
        default=None,
        help="the name of the config file",
    )
    args = parser.parse_args()
    main(args.c)
