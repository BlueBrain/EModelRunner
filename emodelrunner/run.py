"""Create python recordings."""

import argparse

from bluepyopt import ephys

from emodelrunner.create_cells import create_cell_using_config
from emodelrunner.create_protocols import SSCXProtocols
from emodelrunner.load import (
    load_sscx_config,
    get_prot_args,
    get_release_params,
)
from emodelrunner.output import write_current
from emodelrunner.output import write_responses


def main(config_path):
    """Main.

    Args:
        config_path (str): path to config file
            The config file should have '.ini' suffix
    """
    # pylint: disable=too-many-locals
    config = load_sscx_config(config_path=config_path)

    cell = create_cell_using_config(config)
    release_params = get_release_params(config)

    cvode_active = config.getboolean("Sim", "cvode_active")

    # simulator
    dt = config.getfloat("Sim", "dt")
    sim = ephys.simulators.NrnSimulator(dt=dt, cvode_active=cvode_active)

    # create protocols
    add_synapses = config.getboolean("Synapses", "add_synapses")
    prot_args = get_prot_args(config)

    sscx_protocols = SSCXProtocols(add_synapses, prot_args, cell)
    ephys_protocols = sscx_protocols.get_ephys_protocols()

    # run
    print("Python Recordings Running...")
    responses = ephys_protocols.run(
        cell_model=cell, param_values=release_params, sim=sim
    )

    currents = sscx_protocols.get_stim_currents(responses)

    # write responses
    output_dir = config.get("Paths", "output_dir")
    write_responses(responses, output_dir)
    write_current(currents, output_dir)

    print("Python Recordings Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config_path",
        default=None,
        help="the path to the config file.",
    )
    args = parser.parse_args()
    main(config_path=args.config_path)
