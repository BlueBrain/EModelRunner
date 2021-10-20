"""Contains tests for the synapse plasticity workflow (only postcell & pair sim)."""
import os

import h5py
import numpy as np

from emodelrunner.run_pairsim import run as run_pairsim
from emodelrunner.run_synplas import run as run_synplas
from tests.utils import compile_mechanisms, cwd

data_dir = os.path.join("tests", "data")
example_dir = os.path.join("examples", "synplas_sample_dir")


def remove_all_outputs():
    with cwd(example_dir):
        filepath = "output_1Hz_10ms.h5"
        if os.path.exists(filepath):
            os.remove(filepath)


def check_output(threshold_v=0.1):
    """Checks output with respect to the original run."""
    original_path = os.path.join(data_dir, "original.h5")
    new_path = os.path.join(example_dir, "output_1Hz_10ms.h5")

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
        compile_mechanisms()
        run_synplas(config_path="config/config_1Hz_10ms.ini")

    check_output(threshold_v=0.1)


def test_pairsim_voltages():
    """Test to compare the voltages produced with BPO and bglibpy for the pair simulation.

    The cells are run with subprocess, because if they are called directly from the module,
    neuron 'remembers' the cell template and that could make the other tests fail.
    """
    remove_all_outputs()

    with cwd(example_dir):
        compile_mechanisms()
        run_pairsim(config_path="config/config_1Hz_10ms.ini")

    check_output(threshold_v=1.0)
