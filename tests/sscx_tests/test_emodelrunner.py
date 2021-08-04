"""Contains tests for the workflow."""
# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=import-error
import os
from pathlib import Path
import json
import numpy as np
import subprocess

from emodelrunner.create_hoc import get_hoc, write_hocs
from emodelrunner.load import (
    load_config,
    get_hoc_paths_args,
)
from emodelrunner.run import main as run_emodel
from tests.utils import compile_mechanisms, cwd

data_dir = os.path.join("tests", "data")
example_dir = os.path.join("examples", "sscx_sample_dir")


def test_voltages():
    """Test to compare the voltages produced via python and hoc.

    The cells are run with subprocess, because if they are called directly from the module,
    neuron 'remembers' the cell template and that could make the other tests fail.
    """
    threshold = 1e-5

    # rewrite hocs and run cells
    run_hoc_filename = "run.hoc"
    config_path = "config/config_allsteps.ini"

    with cwd(example_dir):
        # write hocs
        config = load_config(config_path=config_path)
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(
            config=config, syn_temp_name="hoc_synapses"
        )
        hoc_paths = get_hoc_paths_args(config)
        write_hocs(hoc_paths, cell_hoc, simul_hoc, run_hoc, run_hoc_filename, syn_hoc)

        subprocess.call(["sh", "./run_hoc.sh"])
        run_emodel(config_path=config_path)

    for idx in range(3):
        hoc_path = os.path.join(
            example_dir, "hoc_recordings", "soma_voltage_step%d.dat" % (idx + 1)
        )
        py_path = os.path.join(
            example_dir, "python_recordings", "soma_voltage_step%d.dat" % (idx + 1)
        )

        hoc_voltage = np.loadtxt(hoc_path)
        py_voltage = np.loadtxt(py_path)

        rms = np.sqrt(np.mean((hoc_voltage[:, 1] - py_voltage[:, 1]) ** 2))
        assert rms < threshold


def test_synapses(config_path="config/config_synapses.ini"):
    """Test to compare the output of cell with synapses between our run.py and bglibpy.

    Attributes:
        configfile: the configuration file of the emodel.
    """

    threshold = 0.05

    # load bglibpy data
    bg_v = np.loadtxt(os.path.join(data_dir, "bglibpy_voltage.dat"))

    with cwd(example_dir):
        compile_mechanisms()
        run_emodel(config_path=config_path)

    py_path = os.path.join(example_dir, "python_recordings", "soma_voltage_vecstim.dat")
    py_v = np.loadtxt(py_path)

    # compare
    rms = np.sqrt(np.mean((bg_v - py_v[:, 1]) ** 2))
    assert rms < threshold


def test_synapses_hoc_vs_py_script(config_path="config/config_synapses.ini"):
    """Test to compare the voltages produced via python and hoc.

    Attributes:
        configfile : name of config file in /config to use when running script / creating hoc
    """
    threshold = 1e-5

    # rewrite hocs and run cells
    run_hoc_filename = "run.hoc"

    # start with hoc, to compile mechs
    with cwd(example_dir):
        # write hocs
        config = load_config(config_path=config_path)
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(
            config=config, syn_temp_name="hoc_synapses"
        )
        hoc_paths = get_hoc_paths_args(config)
        write_hocs(hoc_paths, cell_hoc, simul_hoc, run_hoc, run_hoc_filename, syn_hoc)

        subprocess.call(["sh", "./run_hoc.sh"])
        run_emodel(config_path=config_path)

    # load output
    hoc_path = os.path.join(example_dir, "hoc_recordings", "soma_voltage_vecstim.dat")
    py_path = os.path.join(example_dir, "python_recordings", "soma_voltage_vecstim.dat")

    hoc_voltage = np.loadtxt(hoc_path)
    py_voltage = np.loadtxt(py_path)

    # check rms
    rms = np.sqrt(np.mean((hoc_voltage[:, 1] - py_voltage[:, 1]) ** 2))
    assert rms < threshold
