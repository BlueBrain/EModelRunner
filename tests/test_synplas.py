"""Contains tests for the synapse plasticity workflow (only postcell & pair sim)."""
import os
import subprocess

import h5py
import numpy as np

from tests.utils import cwd

data_dir = os.path.join("tests", "data")
example_dir = os.path.join("tests", "synplas_sample_dir")


def remove_all_outputs():
    with cwd(example_dir):
        filepath = "output.h5"
        if os.path.exists(filepath):
            os.remove(filepath)


def check_output(threshold_v=0.1, threshold_other=0.5):
    """Checks output with respect to the original run."""
    original_path = os.path.join(data_dir, "original.h5")
    new_path = os.path.join(example_dir, "output.h5")

    with h5py.File(original_path, "r") as original:
        with h5py.File(new_path, "r") as new:
            original_t = original["t"][()]
            original_v = original["v"][()]
            new_t = new["t"][()]

            new_v = np.interp(original_t, new_t, new["v"][()])
            rms = np.sqrt(np.mean((original_v - new_v) ** 2))
            assert rms < threshold_v


def test_voltages():
    """Test to compare the voltages produced with BPO with the ones produced by bglibpy.

    The cells are run with subprocess, because if they are called directly from the module,
    neuron 'remembers' the cell template and that could make the other tests fail.
    """
    remove_all_outputs()

    with cwd(example_dir):
        subprocess.call(["sh", "run.sh"])

    check_output(threshold_v=0.1, threshold_other=1.0)


def test_pairsim_voltages():
    """Test to compare the voltages produced with BPO and bglibpy for the pair simulation.

    The cells are run with subprocess, because if they are called directly from the module,
    neuron 'remembers' the cell template and that could make the other tests fail.
    """
    remove_all_outputs()

    with cwd(example_dir):
        subprocess.call(["sh", "run_pairsim.sh"])

    check_output(threshold_v=1.0, threshold_other=10.0)
