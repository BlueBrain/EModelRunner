"""Unit tests for the functions of the GUI's simulator."""

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

from bluepyopt.ephys.simulators import NrnSimulator

from emodelrunner.GUI_utils.simulator import (
    section_coordinate_3d,
    get_pos_and_color,
    get_step_data,
    get_holding_data,
)

sim = NrnSimulator()


def test_section_coordinate_3d():
    """Test section_coordinate_3d function."""
    dend = sim.neuron.h.Section(name="dend")

    # test no 3d location in section
    assert section_coordinate_3d(dend, 0.5) is None

    # create dend as cylinder extending in x direction
    size = 101
    xvec = sim.neuron.h.Vector(np.linspace(0, 100, size))
    yvec = sim.neuron.h.Vector(np.full(size, 0.0))
    zvec = sim.neuron.h.Vector(np.full(size, 0.0))
    dvec = sim.neuron.h.Vector(np.full(size, 500.0))
    sim.neuron.h.pt3dadd(xvec, yvec, zvec, dvec, sec=dend)

    # test segment position < 0 or > 1
    assert section_coordinate_3d(dend, -0.5) is None
    assert section_coordinate_3d(dend, 1.5) is None
    # test segment position in 'arc3d' 3d location list
    assert section_coordinate_3d(dend, 0.5) == [50.0, 0.0, 0.0]
    # test segment position not in 'arc3d' 3d location list
    assert section_coordinate_3d(dend, 0.505) == [50.5, 0.0, 0.0]


def test_get_pos_and_color():
    """Test get_pos_and_color function."""
    dend = sim.neuron.h.Section(name="dend")

    # test no 3d location in section
    assert get_pos_and_color(dend, 0.5, 100) is None

    # create dend as cylinder extending in x direction
    size = 101
    xvec = sim.neuron.h.Vector(np.linspace(0, 100, size))
    yvec = sim.neuron.h.Vector(np.full(size, 0.0))
    zvec = sim.neuron.h.Vector(np.full(size, 0.0))
    dvec = sim.neuron.h.Vector(np.full(size, 500.0))
    sim.neuron.h.pt3dadd(xvec, yvec, zvec, dvec, sec=dend)

    assert get_pos_and_color(dend, 0.5, 14) == [50.0, 0.0, 0.0, 0]
    assert get_pos_and_color(dend, 0.5, 140) == [50.0, 0.0, 0.0, 1]
    assert get_pos_and_color(dend, 0.5, 100) == [50.0, 0.0, 0.0, 1]


def test_get_step_data():
    """Test get_step_data function."""
    steps = []
    default_step = 0
    step = {"delay": 70.0, "amp": 0.2, "duration": 200.0, "totduration": 300.0}
    tot_dur, delay, duration = get_step_data(steps, step, default_step)
    assert (tot_dur, delay, duration) == (300.0, 70.0, 200.0)
    assert steps == [0.2]

    # case amp == default step: amp is not added to steps
    step = {"delay": 70.0, "amp": 0.0, "duration": 200.0, "totduration": 300.0}
    get_step_data(steps, step, default_step)
    assert steps == [0.2]

    # list case
    step = [
        {"delay": 70.0, "amp": 0.0, "duration": 200.0, "totduration": 500.0},
        {"delay": 300.0, "amp": 0.5, "duration": 100.0, "totduration": 500.0},
    ]
    tot_dur, delay, duration = get_step_data(steps, step, default_step)
    assert (tot_dur, delay, duration) == (500.0, 300.0, 100.0)
    assert steps == [0.2, 0.5]


def test_get_holding_data():
    """Test get_holding_data function."""
    holdings = []
    tot_dur = 300.0
    default_hold = 0.0

    # amp is None case
    stim_data = {
        "holding": {
            "delay": 10.0,
            "amp": None,
            "duration": 400.0,
            "totduration": 400.0,
        }
    }
    delay, duration = get_holding_data(holdings, stim_data, tot_dur, default_hold)
    assert holdings == []
    assert delay == 10.0
    assert duration == 400.0

    # amp is default holding case
    stim_data = {
        "holding": {
            "delay": 0.0,
            "amp": 0.0,
            "duration": 400.0,
            "totduration": 400.0,
        }
    }
    delay, duration = get_holding_data(holdings, stim_data, tot_dur, default_hold)
    assert holdings == []

    # no holding data case
    stim_data = {}
    delay, duration = get_holding_data(holdings, stim_data, tot_dur, default_hold)
    assert holdings == []
    assert delay == 0.0
    assert duration == tot_dur

    # amp is a value
    stim_data = {
        "holding": {
            "delay": 0.0,
            "amp": 0.2,
            "duration": 400.0,
            "totduration": 400.0,
        }
    }
    delay, duration = get_holding_data(holdings, stim_data, tot_dur, default_hold)
    assert holdings == [0.2]
