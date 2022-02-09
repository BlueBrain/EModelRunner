"""Contains tests for the synapse plasticity workflow (only postcell & pair sim)."""

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

import os

import h5py
import numpy as np

from emodelrunner.synplas_analysis import Experiment, epsp_slope
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

    check_output(threshold_v=0.07)


def test_analysis():
    """Test analysis script."""
    # here, the synapses responses are smaller after the stimuli
    exp = Experiment(
        data=os.path.join(data_dir, "original.h5"),
        c01duration=5,
        c02duration=5,
        period=5,
    )

    # check that synapses are smaller after the stimuli
    assert exp.compute_epsp_ratio(10, method="amplitude") < 1
    assert exp.compute_epsp_ratio(10, method="slope") < 1

    # check that we collect all 60 synapse responses
    assert len(exp.epsp["C01"]) == 60
    assert len(exp.epsp["C02"]) == 60

    # check that synapses are smaller after the stimuli
    epsp_interval = exp.compute_epsp_interval(5)
    assert epsp_interval["C01"]["avg"] > epsp_interval["C02"]["avg"]

    # check that all interpolated traces have the same number of data points
    for trace in exp.cxtrace["C01"]:
        assert len(trace) == len(exp.cxtrace["t"])
    for trace in exp.cxtrace["C02"]:
        assert len(trace) == len(exp.cxtrace["t"])

    # check that EPSP slope is positive
    assert epsp_slope(exp.cxtrace["C01"][0]) > 0
