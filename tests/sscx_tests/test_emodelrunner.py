"""Contains tests for the workflow."""

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
    load_sscx_config,
    get_hoc_paths_args,
)
from emodelrunner.protocols import (
    StepProtocol,
    StepThresholdProtocol,
    RampProtocol,
    RampThresholdProtocol,
)
from emodelrunner.run import main as run_emodel
from tests.utils import compile_mechanisms, cwd

data_dir = os.path.join("tests", "data")
example_dir = os.path.join("examples", "sscx_sample_dir")


def compare_hoc_and_py(filename, threshold):
    """Compare hoc and py datafiles."""
    hoc_path = os.path.join(example_dir, "hoc_recordings", filename)
    py_path = os.path.join(example_dir, "python_recordings", filename)

    hoc_voltage = np.loadtxt(hoc_path)
    py_voltage = np.loadtxt(py_path)

    # check rms
    rms = np.sqrt(np.mean((hoc_voltage[:, 1] - py_voltage[:, 1]) ** 2))
    assert rms < threshold


def test_voltages():
    """Test to compare the voltages produced via python and hoc.

    The cells are run with subprocess, because if they are called directly from the module,
    neuron 'remembers' the cell template and that could make the other tests fail.
    """
    threshold = 1e-5

    # rewrite hocs and run cells
    config_path = "config/config_allsteps.ini"

    with cwd(example_dir):
        # write hocs
        config = load_sscx_config(config_path=config_path)
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(config=config)
        hoc_paths = get_hoc_paths_args(config)
        write_hocs(hoc_paths, cell_hoc, simul_hoc, run_hoc, syn_hoc)

        subprocess.call(["sh", "./run_hoc.sh"])
        run_emodel(config_path=config_path)

    for idx in range(3):
        filename = "L5TPCa.Step_{}.soma.v.dat".format(150 + idx * 50)
        compare_hoc_and_py(filename, threshold)


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

    py_path = os.path.join(
        example_dir, "python_recordings", "L5TPCa.Synapses_Vecstim.soma.v.dat"
    )
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
    # start with hoc, to compile mechs
    with cwd(example_dir):
        # write hocs
        config = load_sscx_config(config_path=config_path)
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(config=config)
        hoc_paths = get_hoc_paths_args(config)
        write_hocs(hoc_paths, cell_hoc, simul_hoc, run_hoc, syn_hoc)

        subprocess.call(["sh", "./run_hoc.sh"])
        run_emodel(config_path=config_path)

    compare_hoc_and_py("L5TPCa.Synapses_Vecstim.soma.v.dat", threshold)


def test_recipe_protocols():
    """Verify that recipe protocols produce expected voltage and current outputs."""
    config_path = "config/config_recipe_protocols.ini"

    with cwd(example_dir):
        run_emodel(config_path=config_path)

    output_dir = os.path.join(example_dir, "python_recordings")
    output_files = [
        "L5TPCa.Step_150.soma.v.dat",
        "L5TPCa.Step_200.soma.v.dat",
        "L5TPCa.Step_280.soma.v.dat",
        "L5TPCa.APWaveform_320.soma.v.dat",
        "L5TPCa.bAP.soma.v.dat",
        "L5TPCa.bAP.dend1.v.dat",
        "L5TPCa.bAP.dend2.v.dat",
        "L5TPCa.bAP.ca_soma.cai.dat",
        "L5TPCa.bAP.ca_ais.cai.dat",
        "L5TPCa.bAP.ca_prox_apic.cai.dat",
        "L5TPCa.bAP.ca_prox_basal.cai.dat",
        "L5TPCa.IV_-100.soma.v.dat",
        "L5TPCa.Rin.soma.v.dat",
        "L5TPCa.RMP.soma.v.dat",
        "L5TPCa.SpikeRec_600.soma.v.dat",
        "L5TPCa.bpo_holding_current.dat",
        "L5TPCa.bpo_threshold_current.dat",
        "current_L5TPCa.Step_150.dat",
        "current_L5TPCa.Step_200.dat",
        "current_L5TPCa.Step_280.dat",
        "current_L5TPCa.APWaveform_320.dat",
        "current_L5TPCa.bAP.dat",
        "current_L5TPCa.IV_-100.dat",
        "current_L5TPCa.RMP.dat",
        "current_L5TPCa.SpikeRec_600.dat",
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
    step_curr_dict = step_prot.generate_current()
    step_curr = step_curr_dict["current_"]["current"]
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
    step_thres_curr_dict = step_prot_thres.generate_current(
        threshold_current=1.0, holding_current=-0.2
    )
    step_thres_curr = step_thres_curr_dict["current_"]["current"]
    assert np.all(step_thres_curr[:200] == np.full(200, -0.2))
    assert np.all(step_thres_curr[900:] == np.full(100, -0.2))
    assert np.all(step_thres_curr[200:900] == np.full(700, 0.3))

    # step stimulus vs 'flat' ramp
    flat_ramp_prot = RampProtocol(
        name="flat_ramp",
        ramp_stimulus=flat_ramp,
        holding_stimulus=hold_stim,
    )
    flat_ramp_curr_dict = flat_ramp_prot.generate_current()
    flat_ramp_curr = flat_ramp_curr_dict["current_"]["current"]
    assert np.all(step_curr == flat_ramp_curr)

    # threshold step stimulus vs threshold 'flat' ramp
    flat_thres_ramp_prot = RampThresholdProtocol(
        name="flat_thres_ramp",
        ramp_stimulus=flat_ramp,
        holding_stimulus=hold_stim,
        thresh_perc_start=50,
        thresh_perc_end=50,
    )
    flat_thres_ramp_curr_dict = flat_thres_ramp_prot.generate_current(
        threshold_current=1.0, holding_current=-0.2
    )
    flat_thres_ramp_curr = flat_thres_ramp_curr_dict["current_"]["current"]
    assert np.all(step_thres_curr == flat_thres_ramp_curr)

    # no delay ramp
    ramp_prot = RampProtocol(
        name="no_delay_ramp",
        ramp_stimulus=no_delay_ramp,
        holding_stimulus=hold_stim,
    )
    ramp_curr_dict = ramp_prot.generate_current()
    ramp_curr = ramp_curr_dict["current_"]["current"]
    assert np.all(ramp_curr == np.linspace(-0.1, 0.9, 1001)[:-1])

    # no delay thres ramp
    ramp_thres_prot = RampThresholdProtocol(
        name="no_delay_thres_ramp",
        ramp_stimulus=no_delay_ramp,
        holding_stimulus=hold_stim,
        thresh_perc_start=0,
        thresh_perc_end=100,
    )
    ramp_thres_curr_dict = ramp_thres_prot.generate_current(
        threshold_current=0.5, holding_current=-0.2
    )
    ramp_thres_curr = ramp_thres_curr_dict["current_"]["current"]
    assert np.all(ramp_thres_curr == np.linspace(-0.2, 0.3, 1001)[:-1])


def test_multiprotocols_hoc_vs_py_script(
    config_path="config/config_multiprotocols.ini",
):
    """Compare voltages from python and hoc for successive protocols.

    Attributes:
        configfile : name of config file in /config to use when running script / creating hoc
    """
    threshold = 1e-5

    # rewrite hocs and run cells
    # start with hoc, to compile mechs
    with cwd(example_dir):
        # write hocs
        config = load_sscx_config(config_path=config_path)
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(config=config)
        hoc_paths = get_hoc_paths_args(config)
        write_hocs(hoc_paths, cell_hoc, simul_hoc, run_hoc, syn_hoc)

        subprocess.call(["sh", "./run_hoc.sh"])
        run_emodel(config_path=config_path)

    compare_hoc_and_py("L5TPCa.Ramp.soma.v.dat", threshold)
    compare_hoc_and_py("L5TPCa.Synapses_Netstim.soma.v.dat", threshold)
    compare_hoc_and_py("L5TPCa.MultiStepProtocolNoHolding.soma.v.dat", threshold)

    compare_hoc_and_py("L5TPCa.Ramp.ca_soma.cai.dat", threshold)
    compare_hoc_and_py("L5TPCa.Ramp.ca_ais.cai.dat", threshold)
    compare_hoc_and_py("L5TPCa.Ramp.ca_prox_basal.cai.dat", threshold)
    compare_hoc_and_py("L5TPCa.Ramp.dend1.v.dat", threshold)
