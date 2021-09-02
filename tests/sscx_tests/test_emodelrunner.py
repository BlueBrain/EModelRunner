"""Contains tests for the workflow."""
# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=import-error
import os
import numpy as np
import subprocess

import pytest

from bluepyopt import ephys
from emodelrunner.create_hoc import get_hoc, write_hocs
from emodelrunner.load import (
    load_config,
    get_hoc_paths_args,
)
from emodelrunner.recipe_protocols.protocols import (
    StepProtocol,
    StepThresholdProtocol,
    RampProtocol,
    RampThresholdProtocol,
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


def test_recipe_protocols():
    """Verify that recipe protocols produce expected voltage and current outputs."""
    config_path = "config/config_recipe_protocols.ini"

    with cwd(example_dir):
        run_emodel(config_path=config_path)

    output_dir = os.path.join(example_dir, "python_recordings")
    output_files = [
        "current_APWaveform_320.dat",
        "current_Step_200.dat",
        "soma_voltage_L5TPCa.RMP.soma.v.dat",
        "soma_voltage_L5TPCa.Step_280.soma.v.dat",
        "soma_voltage_L5TPCa.bAP.dend1.v.dat",
        "current_IV_-100.dat",
        "current_Step_280.dat",
        "soma_voltage_L5TPCa.Rin.soma.v.dat",
        "soma_voltage_L5TPCa.bAP.ca_ais.v.dat",
        "soma_voltage_L5TPCa.bAP.dend2.v.dat",
        "current_RMP.dat",
        "current_bAP.dat",
        "soma_voltage_L5TPCa.SpikeRec_600.soma.v.dat",
        "soma_voltage_L5TPCa.bAP.ca_prox_apic.v.dat",
        "soma_voltage_L5TPCa.bAP.soma.v.dat",
        "current_SpikeRec_600.dat",
        "soma_voltage_L5TPCa.APWaveform_320.soma.v.dat",
        "soma_voltage_L5TPCa.Step_150.soma.v.dat",
        "soma_voltage_L5TPCa.bAP.ca_prox_basal.v.dat",
        "soma_voltage_L5TPCa.bpo_holding_current.dat",
        "current_Step_150.dat",
        "soma_voltage_L5TPCa.IV_-100.soma.v.dat",
        "soma_voltage_L5TPCa.Step_200.soma.v.dat",
        "soma_voltage_L5TPCa.bAP.ca_soma.v.dat",
        "soma_voltage_L5TPCa.bpo_threshold_current.dat",
    ]

    for fname in output_files:
        assert os.path.isfile(os.path.join(output_dir, fname))


def test_generate_current():
    """Test generate current fcts of recipe protocols."""
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma", seclist_name="somatic", sec_index=0, comp_x=0.5
    )
    step_stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=0.3,
        step_delay=20,
        step_duration=70,
        location=soma_loc,
        total_duration=100,
    )
    hold_stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=-0.1,
        step_delay=0,
        step_duration=100,
        location=soma_loc,
        total_duration=100,
    )
    flat_ramp = ephys.stimuli.NrnRampPulse(
        ramp_amplitude_start=0.3,
        ramp_amplitude_end=0.3,
        ramp_delay=20,
        ramp_duration=70,
        location=soma_loc,
        total_duration=100,
    )
    no_delay_ramp = ephys.stimuli.NrnRampPulse(
        ramp_amplitude_start=0.0,
        ramp_amplitude_end=1.0,
        ramp_delay=0,
        ramp_duration=100,
        location=soma_loc,
        total_duration=100,
    )

    # step stimulus
    step_prot = StepProtocol(
        name="step",
        step_stimuli=[step_stim],
        holding_stimulus=hold_stim,
    )
    _, step_curr = step_prot.generate_current()
    assert np.all(step_curr[:200] == np.full(200, -0.1))
    assert np.all(step_curr[900:] == np.full(100, -0.1))
    assert np.all(step_curr[200:900] == np.full(700, pytest.approx(0.2)))

    # step threshold
    step_prot_thres = StepThresholdProtocol(
        name="step_thres",
        step_stimuli=[step_stim],
        holding_stimulus=hold_stim,
        thresh_perc=50,
    )
    _, step_thres_curr = step_prot_thres.generate_current(
        threshold_current=1.0, holding_current=-0.2
    )
    assert np.all(step_thres_curr[:200] == np.full(200, -0.2))
    assert np.all(step_thres_curr[900:] == np.full(100, -0.2))
    assert np.all(step_thres_curr[200:900] == np.full(700, 0.3))

    # step stimulus vs 'flat' ramp
    flat_ramp_prot = RampProtocol(
        name="flat_ramp",
        ramp_stimulus=flat_ramp,
        holding_stimulus=hold_stim,
    )
    _, flat_ramp_curr = flat_ramp_prot.generate_current()
    assert np.all(step_curr == flat_ramp_curr)

    # threshold step stimulus vs threshold 'flat' ramp
    flat_thres_ramp_prot = RampThresholdProtocol(
        name="flat_thres_ramp",
        ramp_stimulus=flat_ramp,
        holding_stimulus=hold_stim,
        thresh_perc_start=50,
        thresh_perc_end=50,
    )
    _, flat_thres_ramp_curr = flat_thres_ramp_prot.generate_current(
        threshold_current=1.0, holding_current=-0.2
    )
    assert np.all(step_thres_curr == flat_thres_ramp_curr)

    # no delay ramp
    ramp_prot = RampProtocol(
        name="no_delay_ramp",
        ramp_stimulus=no_delay_ramp,
        holding_stimulus=hold_stim,
    )
    _, ramp_curr = ramp_prot.generate_current()
    assert np.all(ramp_curr == np.linspace(-0.1, 0.9, 1001)[:-1])

    # no delay thres ramp
    ramp_thres_prot = RampThresholdProtocol(
        name="no_delay_thres_ramp",
        ramp_stimulus=no_delay_ramp,
        holding_stimulus=hold_stim,
        thresh_perc_start=0,
        thresh_perc_end=100,
    )
    _, ramp_thres_curr = ramp_thres_prot.generate_current(
        threshold_current=0.5, holding_current=-0.2
    )
    assert np.all(ramp_thres_curr == np.linspace(-0.2, 0.3, 1001)[:-1])
