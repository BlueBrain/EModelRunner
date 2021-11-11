"""Functions to write output."""

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

import os
import json

import h5py
import numpy as np


def write_responses(responses, output_dir):
    """Write each response in a file.

    Args:
        responses (dict): time and recorded value of each recording
            Should have structure "key": {"time": time, "voltage": response}
            Note that all response have a "voltage" field, even if the recorded value
            was not the voltage
        output_dir (str): path to the output repository
    """
    for key, resp in responses.items():
        output_path = os.path.join(output_dir, key + ".dat")

        # holding & threshold current cases for recipe protocols
        if isinstance(resp, (float, np.float)):
            np.savetxt(output_path, np.array([resp]))
        else:
            time = np.array(resp["time"])
            soma_voltage = np.array(resp["voltage"])

            np.savetxt(output_path, np.transpose(np.vstack((time, soma_voltage))))


def write_current(currents, output_dir):
    """Write currents into separate files.

    Args:
        currents (dict): time and trace to each recording
            Should have structure "key": {"time": time, "current": current}
        output_dir (str): path to the output repository
    """
    for key, curr_dict in currents.items():
        output_path = os.path.join(output_dir, key + ".dat")
        np.savetxt(
            output_path,
            np.transpose(np.vstack((curr_dict["time"], curr_dict["current"]))),
        )


def write_synplas_output(
    responses,
    pre_spike_train,
    output_path="./output.h5",
    syn_prop_path="synapses/synapse_properties.json",
):
    """Write output as h5.

    Args:
        responses (dict): responses of the postsynaptic cell
        pre_spike_train (list): times at which the synapses fire (ms)
        output_path (str): path to the (postsynaptic data) output file
        syn_prop_path (str): path to the synapse properties file
    """
    results = {"prespikes": pre_spike_train}
    # add synprop
    if os.path.isfile(syn_prop_path):
        with open(syn_prop_path, "r", encoding="utf-8") as f:
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
    h5file = h5py.File(output_path, "w")
    for key, result in results.items():
        if key == "synprop":
            h5file.attrs.update(results["synprop"])
        else:
            h5file.create_dataset(
                key,
                data=result,
                chunks=True,
                compression="gzip",
                compression_opts=9,
            )
    h5file.close()


def write_synplas_precell_output(
    responses,
    protocol_name,
    precell_output_path="./output_precell.h5",
):
    """Write precell output as h5.

    Args:
        responses (dict): responses of the presynaptic cell
        protocol_name (str): name of the presynaptic protocol
        precell_output_path (str): path to the presynaptic data output file
    """
    results = {}

    # add responses
    results["t"] = np.array(responses[protocol_name]["time"])
    results["v"] = np.array(responses[protocol_name]["voltage"])

    # Store results
    h5file = h5py.File(precell_output_path, "w")
    for key, result in results.items():
        h5file.create_dataset(
            key,
            data=result,
            chunks=True,
            compression="gzip",
            compression_opts=9,
        )
    h5file.close()
