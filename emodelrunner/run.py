"""Create python recordings."""

import argparse

from bluepyopt import ephys

from emodelrunner.create_cells import create_cell_using_config
from emodelrunner.create_protocols import SSCXProtocols
from emodelrunner.load import (
    load_config,
    get_release_params,
    get_step_prot_args,
    get_syn_prot_args,
)
from emodelrunner.output import write_current
from emodelrunner.output import write_responses


def main(config_file):
    """Main."""
    # pylint: disable=too-many-locals
    config = load_config(filename=config_file)

    cell = create_cell_using_config(config)
    release_params = get_release_params(config)

    cvode_active = config.getboolean("Sim", "cvode_active")

    # simulator
    dt = config.getfloat("Sim", "dt")
    sim = ephys.simulators.NrnSimulator(dt=dt, cvode_active=cvode_active)

    # create protocols
    step_stim = config.getboolean("Protocol", "step_stimulus")
    add_synapses = config.getboolean("Synapses", "add_synapses")
    step_args = get_step_prot_args(config)
    syn_args = get_syn_prot_args(config)

    sscx_protocols = SSCXProtocols(
        step_args, syn_args, step_stim, add_synapses, cvode_active, cell
    )
    ephys_protocols = sscx_protocols.get_ephys_protocols()
    currents = sscx_protocols.get_stim_currents()

    # run
    print("Python Recordings Running...")

    responses = ephys_protocols.run(
        cell_model=cell, param_values=release_params, sim=sim
    )

    # write responses
    output_dir = config.get("Paths", "output_dir")
    output_file = config.get("Paths", "output_file")
    write_responses(responses, output_dir, output_file)
    write_current(currents, output_dir)

    print("Python Recordings Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--c",
        default=None,
        help="the name of the config file to be looked under ./config directory",
    )
    args = parser.parse_args()
    main(args.c)
