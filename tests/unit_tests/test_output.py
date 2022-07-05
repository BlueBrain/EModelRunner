"""Unit tests for output.py."""

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

import h5py
from pathlib import Path
import numpy as np

import pytest

from emodelrunner.output import (
    write_responses,
    write_current,
    write_synplas_output,
    write_synplas_precell_output,
)

output_dir = Path("tests/output")


@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    """Fixture to execute asserts before and after a test is run"""
    output_dir.mkdir(parents=True, exist_ok=True)
    yield


def test_write_responses():
    """Test write_responses function."""
    responses = {
        "test_wr_none": None,
        "test_wr_float": 0.12,
        "test_wr_np_float": np.float(0.1),
        "test_wr_resp": {"time": [1.0, 2.0, 3.0], "voltage": [-80.0, -80.0, -79.0]},
    }
    write_responses(responses, output_dir)

    assert not (output_dir / "test_wr_none.dat").is_file()

    assert (output_dir / "test_wr_float.dat").is_file()
    assert np.loadtxt(output_dir / "test_wr_float.dat") == 0.12

    assert (output_dir / "test_wr_np_float.dat").is_file()
    assert np.loadtxt(output_dir / "test_wr_np_float.dat") == 0.1

    assert (output_dir / "test_wr_resp.dat").is_file()
    assert np.array_equal(
        np.loadtxt(output_dir / "test_wr_resp.dat"),
        np.array([[1.0, -80.0], [2.0, -80.0], [3.0, -79.0]]),
    )


def test_write_current():
    """Test write_current function."""
    currents = {
        "test_wc_currents": {"time": [1.0, 2.0, 3.0], "current": [-80.0, -80.0, -79.0]}
    }
    write_current(currents, output_dir)

    assert (output_dir / "test_wc_currents.dat").is_file()
    assert np.array_equal(
        np.loadtxt(output_dir / "test_wc_currents.dat"),
        np.array([[1.0, -80.0], [2.0, -80.0], [3.0, -79.0]]),
    )


def test_write_synplas_output():
    """Test write_synplas_output function."""
    pre_spike_train = [10.0, 20.0, 30.0]
    syn_prop_path = "tests/unit_tests/data/synprop.json"
    output_path = output_dir / "test_spo.h5"
    responses = {
        "pulse": {"time": [1.0, 2.0, 3.0], "voltage": [-80.0, -80.0, -79.0]},
        "vsyn": [
            {"time": [1.0, 2.0, 3.0], "voltage": [0.0, 0.0, 0.0]},
            {"time": [1.0, 2.0, 3.0], "voltage": [1.0, 1.0, 1.0]},
        ],
    }

    write_synplas_output(responses, pre_spike_train, output_path, syn_prop_path)

    assert (output_path).is_file()
    with h5py.File(output_path, "r") as output_file:
        assert np.array_equal(output_file["t"][()], np.array([1.0, 2.0, 3.0]))
        assert np.array_equal(output_file["v"][()], np.array([-80.0, -80.0, -79.0]))
        assert np.array_equal(
            output_file["vsyn"][()], np.array([[0.0, 1.0], [0.0, 1.0], [0.0, 1.0]])
        )
        assert np.array_equal(output_file["prespikes"], np.array(pre_spike_train))

        assert np.array_equal(
            output_file.attrs["Cpost"], np.array([0.01329, 0.00016, 0.00025])
        )
        assert np.array_equal(
            output_file.attrs["Cpre"], np.array([0.07365, 0.05361, 0.07977])
        )


def test_write_synplas_precell_output():
    """Test write_synplas_precell_output function."""
    output_path = output_dir / "test_sppo.h5"
    responses = {
        "pulse": {"time": [1.0, 2.0, 3.0], "voltage": [-80.0, -80.0, -79.0]},
    }

    write_synplas_precell_output(responses, "pulse", output_path)

    assert (output_path).is_file()
    with h5py.File(output_path, "r") as output_file:
        assert np.array_equal(output_file["t"][()], np.array([1.0, 2.0, 3.0]))
        assert np.array_equal(output_file["v"][()], np.array([-80.0, -80.0, -79.0]))
