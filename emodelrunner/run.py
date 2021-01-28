"""Create python recordings."""

import argparse
import os
import numpy as np

import bluepyopt.ephys as ephys

from emodelrunner.load import load_config
from emodelrunner.protocols import define_protocols
from emodelrunner.create_cells import create_cell


def write_responses(responses, config):
    """Write each response in a file."""
    output_dir = config.get("Paths", "output_dir")
    output_file = config.get("Paths", "output_file")

    for key, resp in responses.items():
        output_path = os.path.join(output_dir, output_file + key + ".dat")

        time = np.array(resp["time"])
        soma_voltage = np.array(resp["voltage"])

        np.savetxt(output_path, np.transpose(np.vstack((time, soma_voltage))))


def main(config_file):
    """Main."""
    config = load_config(filename=config_file)

    cell, release_params, dt_tmp = create_cell(config)

    # simulator
    if config.has_section("Sim") and config.has_option("Sim", "dt"):
        dt = config.getfloat("Sim", "dt")
    else:
        dt = dt_tmp
    sim = ephys.simulators.NrnSimulator(
        dt=dt, cvode_active=config.getboolean("Sim", "cvode_active")
    )

    # create protocols
    protocols = define_protocols(config, cell)

    # run
    print("Python Recordings Running...")

    responses = protocols.run(cell_model=cell, param_values=release_params, sim=sim)

    write_responses(responses, config)

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
