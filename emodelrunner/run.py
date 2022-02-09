"""Create python recordings."""

# Copyright 2020-2022 Blue Brain Project / EPFL

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

from bluepyopt import ephys

from emodelrunner.configuration.configparser import PackageType
from emodelrunner.create_cells import create_cell_using_config
from emodelrunner.protocols.create_protocols import ProtocolBuilder
from emodelrunner.load import (
    load_config,
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
    config = load_config(config_path=config_path)

    cell = create_cell_using_config(config)
    release_params = get_release_params(config)

    cvode_active = config.getboolean("Sim", "cvode_active")

    # simulator
    dt = config.getfloat("Sim", "dt")
    sim = ephys.simulators.NrnSimulator(dt=dt, cvode_active=cvode_active)

    # create protocols
    add_synapses = config.getboolean("Synapses", "add_synapses")
    prot_args = get_prot_args(config)

    if config.package_type == PackageType.sscx:
        protocols = ProtocolBuilder.using_sscx_protocols(add_synapses, prot_args, cell)
    elif config.package_type == PackageType.thalamus:
        protocols = ProtocolBuilder.using_thalamus_protocols(
            add_synapses, prot_args, cell
        )
    else:
        raise ValueError(f"unsupported package type: {config.package_type}")
    ephys_protocols = protocols.get_ephys_protocols()
    # run
    print("Python Recordings Running...")
    responses = ephys_protocols.run(
        cell_model=cell, param_values=release_params, sim=sim, isolate=False
    )

    mtype = config.get("Morphology", "mtype")
    if config.package_type == PackageType.sscx:
        currents = protocols.get_stim_currents(responses, dt)
    elif config.package_type == PackageType.thalamus:
        currents = protocols.get_thalamus_stim_currents(responses, mtype, dt)

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
