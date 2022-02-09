"""Unit tests for synplas_analysis.py."""

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

import numpy as np
import pytest

from emodelrunner.synplas_analysis import (
    Experiment,
    epsp_slope,
    get_epsp_vector,
)

dt = 0.5
v_c01 = np.array([-80, -70, -80, -80, -71, -80])
v_c02 = np.array([-80, -60, -80, -80, -61, -80])
v = np.hstack((v_c01, np.full(6, -80), v_c02))

t = np.arange(0.0, 9.0, dt)
spikes = np.array([0.0, 1.5, 6.0, 7.5])

data = {"t": t, "v": v, "prespikes": spikes}

duration_in_ms = 3.0
duration_in_min = duration_in_ms / 60.0 / 1000.0
period_in_ms = 1.5
period_in_s = period_in_ms / 1000.0

cxs = ["C01", "C02"]
cxspikes = {"C01": spikes[:2], "C02": spikes[2:]}

window = 1.0


def test_Experiment_init():
    """Test constructor of Experiment class."""
    exp = Experiment(data, duration_in_min, duration_in_min, period_in_s)

    assert np.all(exp.t == t)
    assert np.all(exp.v == v)
    assert np.all(exp.spikes == spikes)
    assert exp.duration == {"C01": duration_in_ms, "C02": duration_in_ms}
    assert exp.period == period_in_ms
    assert exp.c01period == period_in_ms
    assert exp.c02period == period_in_ms
    assert exp.epspwindow == 100.0
    assert np.all(exp.cxs == cxs)
    for key, cxspike in exp.cxspikes.items():
        if key == "C01":
            assert np.all(cxspike == cxspikes["C01"])
        elif key == "C02":
            assert np.all(cxspike == cxspikes["C02"])
        else:
            assert False


def test_get_epsp_vector():
    """Test get_epsp_vector function."""
    epsps = get_epsp_vector(t[:6], v_c01, spikes[:2], window)
    assert np.all(epsps == [10, 9])

    bad_v_c01 = np.array([-80, -70, -80, -80, -20, -80])
    with pytest.raises(RuntimeError):
        epsps = get_epsp_vector(t[:6], bad_v_c01, spikes[:2], window)

    bad_window = 2.0
    with pytest.raises(RuntimeError):
        epsps = get_epsp_vector(t[:6], v_c01, spikes[:2], bad_window)


def test_epsp_slope():
    """Test epsp_slope function."""
    exp = Experiment(data, duration_in_min, duration_in_min, period_in_s)
    exp.epspwindow = window

    cx_trace = exp.cxtrace
    slope = epsp_slope(cx_trace["C01"][0])

    # divide by timestep introduced in interpollation in cx_trace computation
    # to have the actual slope
    # turn into an int to remove imprecision
    assert int(slope / 0.025) == 20


def test_epsp():
    """Test epsp property of Experiment class."""
    exp = Experiment(data, duration_in_min, duration_in_min, period_in_s)
    exp.epspwindow = window

    expected_epsp = {"C01": np.array([10, 9]), "C02": np.array([20, 19])}

    for key, epsp in exp.epsp.items():
        if key == "C01":
            assert np.all(epsp == expected_epsp[key])
        elif key == "C02":
            assert np.all(epsp == expected_epsp[key])
        else:
            assert False


def test_cxtrace():
    """Test cxtrace property of Experiment class."""
    exp = Experiment(data, duration_in_min, duration_in_min, period_in_s)
    exp.epspwindow = window

    # expected interpolated traces
    interp_n = 40
    tdense = np.linspace(0, window, int(window * interp_n))
    cxtrace01_0 = np.interp(tdense, [0, 0.5], [-80, -70])
    cxtrace01_1 = np.interp(tdense, [0, 0.5], [-80, -71])
    cxtrace02_0 = np.interp(tdense, [0, 0.5], [-80, -60])
    cxtrace02_1 = np.interp(tdense, [0, 0.5], [-80, -61])

    for key, cxtrace in exp.cxtrace.items():
        if key == "t":
            assert np.all(cxtrace == tdense)
        elif key == "C01":
            np.testing.assert_almost_equal(cxtrace[0], cxtrace01_0)
            np.testing.assert_almost_equal(cxtrace[1], cxtrace01_1)
        elif key == "C02":
            np.testing.assert_almost_equal(cxtrace[0], cxtrace02_0)
            np.testing.assert_almost_equal(cxtrace[1], cxtrace02_1)
        else:
            assert False


def test_compute_epsp_interval():
    """Test epsp_interval method of Experiment class."""
    exp = Experiment(data, duration_in_min, duration_in_min, period_in_s)
    exp.epspwindow = window

    interval = period_in_s / 60.0
    results = exp.compute_epsp_interval(interval)

    assert np.all(results["C01"]["avg"] == [10, 9])
    assert np.all(results["C01"]["sem"] == [0, 0])
    assert np.all(results["C01"]["t"] == [0, 1.5])
    assert np.all(results["C02"]["avg"] == [20, 19])
    assert np.all(results["C02"]["sem"] == [0, 0])
    assert np.all(results["C02"]["t"] == [6, 7.5])


def test_compute_epsp_ratio():
    """Test compute_epsp_ratio method of Experiment class."""
    exp = Experiment(data, duration_in_min, duration_in_min, period_in_s)
    exp.epspwindow = window
    n = 2

    (
        epsp_before,
        epsp_after,
        epsp_ratio,
        epsp_before_std,
        epsp_after_std,
    ) = exp.compute_epsp_ratio(n, "amplitude", full=True)
    assert epsp_before == 9.5
    assert epsp_after == 19.5
    assert epsp_ratio == 19.5 / 9.5
    assert epsp_before_std == 0.5
    assert epsp_after_std == 0.5

    epsp_ratio = exp.compute_epsp_ratio(n, "amplitude", full=False)
    assert epsp_ratio == 19.5 / 9.5

    (
        epsp_before,
        epsp_after,
        epsp_ratio,
        epsp_before_std,
        epsp_after_std,
    ) = exp.compute_epsp_ratio(n, "slope", full=True)
    # slope computation is not exact and depends on interpolation sampling,
    # so check that result is close to expected result
    assert abs(epsp_before - 0.475) < 0.05
    assert abs(epsp_after - 0.975) < 0.05
    assert abs(epsp_ratio - 0.975 / 0.475) < 0.05
    assert epsp_before_std == 0
    assert epsp_after_std == 0

    epsp_ratio = exp.compute_epsp_ratio(n, "slope", full=False)
    assert abs(epsp_ratio - 0.975 / 0.475) < 0.05

    with pytest.raises(ValueError):
        ratio = exp.compute_epsp_ratio(n, "unvalid_method_name")


def test_normalize_time():
    """Test normalize_time method of Experiment class."""
    exp = Experiment(data, duration_in_min)
    t = np.linspace(60000, 180000, 3) + 3

    tnorm = exp.normalize_time(t)
    assert np.all(tnorm == [1, 2, 3])
