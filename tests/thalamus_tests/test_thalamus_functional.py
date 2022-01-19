"""Functional tests for thalamus packages."""

from pathlib import Path

import numpy as np
import pytest

from emodelrunner.run import main as run_emodel
from tests.utils import cwd


class TestMainProtocol:

    @classmethod
    def setup_class(cls):
        """Run the main protocol."""
        cls.example_dir = Path("examples") / "thalamus_sample_dir"
        # rewrite hocs and run cells
        config_path = "config/config_recipe_prots_short.ini"

        with cwd(cls.example_dir):
            run_emodel(config_path=config_path)

    @pytest.mark.parametrize('volt_fname', ["VPL_TC.Step_150.soma.v.dat", "VPL_TC.RMP.soma.v.dat"])
    def test_protocol_voltage(self, volt_fname):
        """Test to reproduce StepProtocol and StepThresholdProtocol voltages.

            VPL_TC.Step_150.soma.v.dat -> StepThresholdProtocol
            VPL_TC.RMP.soma.v.dat -> StepProtocol
        """
        volt_fname = "VPL_TC.Step_150.soma.v.dat"
        ground_truth_dir = Path("tests") / "thalamus_tests" / "data"

        gt_voltage = np.loadtxt(ground_truth_dir / volt_fname)

        reproduced_voltage = np.loadtxt(self.example_dir / "python_recordings" / volt_fname)

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
