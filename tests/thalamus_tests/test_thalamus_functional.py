"""Functional tests for thalamus packages."""

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

from pathlib import Path

import numpy as np
import pytest

from emodelrunner.run import main as run_emodel
from tests.utils import cwd


class TestMainProtocol:
    """Tests for the main thalamus protocol."""

    @classmethod
    def setup_class(cls):
        """Run the main protocol."""
        cls.example_dir = Path("examples") / "thalamus_sample_dir"
        # rewrite hocs and run cells
        config_path = "config/config_recipe_prots_short.ini"

        with cwd(cls.example_dir):
            run_emodel(config_path=config_path)

    @pytest.mark.parametrize(
        "volt_fname", ["VPL_TC.Step_150.soma.v.dat", "VPL_TC.RMP.soma.v.dat"]
    )
    def test_protocol_voltage(self, volt_fname):
        """Test to reproduce StepProtocol and StepThresholdProtocol voltages.

        VPL_TC.Step_150.soma.v.dat -> StepThresholdProtocol
        VPL_TC.RMP.soma.v.dat -> StepProtocol
        """
        ground_truth_dir = Path("tests") / "thalamus_tests" / "data"

        gt_voltage = np.loadtxt(ground_truth_dir / volt_fname)

        reproduced_voltage = np.loadtxt(
            self.example_dir / "python_recordings" / volt_fname
        )

        rms = np.sqrt(np.mean((gt_voltage[:, 1] - reproduced_voltage[:, 1]) ** 2))

        threshold = 1e-7
        assert rms < threshold

    def test_hyp_dep_currents(self):
        """Test to assure hyperpolarization and depolarization currents are different."""
        step_200 = np.loadtxt(
            self.example_dir / "python_recordings" / "current_VPL_TC.Step_200.dat"
        )[:, 1]
        step_200_hyp = np.loadtxt(
            self.example_dir / "python_recordings" / "current_VPL_TC.Step_200_hyp.dat"
        )[:, 1]

        assert [f(step_200) != f(step_200_hyp) for f in [np.min, np.max, np.mean]]

    @staticmethod
    def get_corresponding_current_files(voltage_paths):
        """Returns a list of current files for a list of voltage paths."""
        mtypes = [x.name.split(".")[0] for x in voltage_paths]
        prot_names = [x.name.split(".")[1] for x in voltage_paths]
        return [
            f"current_{mtype}.{prot}.dat" for (mtype, prot) in zip(mtypes, prot_names)
        ]

    def test_current_traces_produced(self):
        """Test to check all produced voltage traces have corresponding current traces."""
        voltage_paths = list(
            Path(self.example_dir / "python_recordings").glob("*v.dat")
        )
        matching_current_names = self.get_corresponding_current_files(voltage_paths)

        current_paths = list(
            Path(self.example_dir / "python_recordings").glob("current*.dat")
        )
        current_names = [x.name for x in current_paths]
        assert set(matching_current_names) == set(current_names)

    def test_voltage_current_size(self):
        """Test to assure the produced voltage and current have the same size."""
        voltage_paths = list(
            Path(self.example_dir / "python_recordings").glob("*v.dat")
        )
        matching_current_fnames = self.get_corresponding_current_files(voltage_paths)
        voltage_fnames = [x.name for x in voltage_paths]

        for voltage_fname, current_fname in zip(
            voltage_fnames, matching_current_fnames
        ):
            voltage = np.loadtxt(self.example_dir / "python_recordings" / voltage_fname)
            current = np.loadtxt(self.example_dir / "python_recordings" / current_fname)
            assert voltage.shape == current.shape
