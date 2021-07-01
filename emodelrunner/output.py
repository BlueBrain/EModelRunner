"""Functions to write output."""
import os
import json

import h5py
import numpy as np


def write_responses(responses, output_dir, output_file):
    """Write each response in a file."""
    for key, resp in responses.items():
        output_path = os.path.join(output_dir, output_file + key + ".dat")

        time = np.array(resp["time"])
        soma_voltage = np.array(resp["voltage"])

        np.savetxt(output_path, np.transpose(np.vstack((time, soma_voltage))))


def write_current(currents, output_dir):
    """Write currents into separate files."""
    for idx, (time, current) in enumerate(currents):
        output_path = os.path.join(output_dir, "current_step" + str(idx + 1) + ".dat")
        np.savetxt(output_path, np.transpose(np.vstack((time, current))))


def write_synplas_output(
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
    output_dir="",
    output_file="output_precell.h5",
):
    """Write output as h5."""
    results = {}

    # add responses
    results["t"] = np.array(responses[protocol_name]["time"])
    results["v"] = np.array(responses[protocol_name]["voltage"])

    # Store results
    output_path = os.path.join(output_dir, output_file)
    h5file = h5py.File(output_path, "w")
    for key, result in results.items():
        h5file.create_dataset(
            key,
            data=result,
            chunks=True,
            compression="gzip",
            compression_opts=9,
        )
    h5file.close()
