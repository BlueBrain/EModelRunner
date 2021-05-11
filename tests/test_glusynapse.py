"""Contains tests for the glusynapse workflow."""
import h5py
import os
import subprocess

import numpy as np

from tests.utils import cwd

data_dir = os.path.join("tests", "data")
example_dir = os.path.join("tests", "glusyn_sample_dir")


def test_voltages():
    """Test to compare the voltages produced with BPO with the ones produced by bglibpy.

    The cells are run with subprocess, because if they are called directly from the module,
    neuron 'remembers' the cell template and that could make the other tests fail.
    """
    threshold = 0.1

    with cwd(example_dir):
        subprocess.call(["sh", "run.sh"])

    original_path = os.path.join(data_dir, "simulation.h5")
    new_path = os.path.join(example_dir, "output.h5")

    with h5py.File(original_path, "r") as original:
        with h5py.File(new_path, "r") as new:
            original_t = original["t"][()]
            new_t = new["t"][()]
            for key, data in original.items():
                if key == "prespikes":
                    assert np.all(data[()] == new[key][()])
                elif key == "v":
                    new_v = np.interp(original_t, new_t, new[key][()])
                    rms = np.sqrt(np.mean((data[()] - new_v) ** 2))
                    assert rms < threshold
                elif key != "t":
                    for i in range(len(data[()][0])):
                        new_data = np.interp(original_t, new_t, new[key][()][:, i])
                        rms = np.sqrt(np.mean((data[()][:, i] - new_data) ** 2))
                        assert rms < threshold

            for key, elem in original.attrs.items():
                assert np.all(elem[()] == new.attrs[key][()])
