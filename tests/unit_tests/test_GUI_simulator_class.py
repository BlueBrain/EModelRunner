"""Unit tests for the NeuronSimulation methods of the GUI's simulator."""

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

from emodelrunner.GUI_utils.simulator import NeuronSimulation
from tests.utils import cwd


example_dir = os.path.join("examples", "sscx_sample_dir")


class TestNeuronSimulation(object):

    """Test class for NeuronSimulation"""

    def setup(self):
        """Setup"""
        with cwd(example_dir):
            self.simulator = NeuronSimulation("config/config_singlestep.ini")

    def test_load_available_pre_mtypes(self):
        """Test load_available_pre_mtypes method."""
        with cwd(example_dir):
            mtypes = self.simulator.load_available_pre_mtypes()

        assert len(mtypes) == 29
        assert mtypes[10] == "L6_LBC"

    def test_create_cell_custom(self):
        """Test create_cell_custom method."""
        with cwd(example_dir):
            cell = self.simulator.create_cell_custom()

        assert cell.name == "cADpyr_L4UPC"
        assert (
            cell.morphology.morphology_path
            == "morphology/dend-C231296A-P4B2_axon-C200897C-P2_-_Scale_x1.000_y0.975_z1.000.asc"
        )
        assert len(cell.mechanisms) > 0
        assert "gNaTgbar_NaTg.axonal" in cell.params.keys()
        assert cell.gid == 2571167
        assert cell.add_synapses is False
        assert cell.fixhp is False

    def test_get_syn_stim(self):
        """Test get_syn_stim method."""
        # None when pre_mtypes is not set
        assert self.simulator.get_syn_stim() is None

        # set pre_mtypes and cell to get a returned net stimulus object
        self.simulator.pre_mtypes = [1]
        with cwd(example_dir):
            self.simulator.cell = self.simulator.create_cell_custom()
            netstim = self.simulator.get_syn_stim()

        assert netstim.interval is None
        assert netstim.number is None
        assert netstim.start is None
        assert netstim.noise == 0
        assert netstim.total_duration == self.simulator.total_duration == 300.0
        assert len(netstim.locations) == 1

    def test_load_protocol(self):
        """Test load_protocol method."""
        prot_name = "test_protocol"
        self.simulator.pre_mtypes = []

        with cwd(example_dir):
            self.simulator.load_protocol(prot_name)

        assert self.simulator.protocol.name == prot_name
        assert len(self.simulator.protocol.stimuli) == 2

        self.simulator.pre_mtypes = [1]
        with cwd(example_dir):
            self.simulator.cell = self.simulator.create_cell_custom()
            self.simulator.load_protocol(prot_name)

        assert len(self.simulator.protocol.stimuli) == 3

    def test_load_synapse_display_data(self):
        """Test load_synapse_display_data method."""
        # instantiate cell
        with cwd(example_dir):
            self.simulator.load_cell_sim()
            self.simulator.sim.mechanisms_directory = "./"
            self.simulator.cell.freeze(self.simulator.release_params)
            self.simulator.cell.instantiate(sim=self.simulator.sim)

        assert self.simulator.syn_display_data is None
        self.simulator.load_synapse_display_data()
        assert len(self.simulator.syn_display_data) == 29
        assert 13 in self.simulator.syn_display_data.keys()
        assert [
            37.45411849626738,
            -83.15094938319406,
            -29.566504944378146,
            1,
        ] in self.simulator.syn_display_data[0]

        # destroy cell
        self.simulator.cell.destroy(sim=self.simulator.sim)
        self.simulator.cell.unfreeze(self.simulator.release_params.keys())
