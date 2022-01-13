"""Functional tests for thalamus packages."""

from pathlib import Path
import numpy as np
from emodelrunner.run import main as run_emodel
from tests.utils import cwd


def test_voltages():
    """Test to reproduce voltage produced in a shortened recipe protocol."""
    threshold = 1e-7

    example_dir = Path("examples") / "thalamus_sample_dir"
    # rewrite hocs and run cells
    config_path = "config/config_recipe_prots_short.ini"

    with cwd(example_dir):
        run_emodel(config_path=config_path)

    volt_fname = "VPL_TC.Step_150.soma.v.dat"
    ground_truth_dir = Path("tests") / "thalamus_tests" / "data"

    gt_voltage = np.loadtxt(ground_truth_dir / volt_fname)

    reproduced_voltage = np.loadtxt(example_dir / "python_recordings" / volt_fname)

    rms = np.sqrt(np.mean((gt_voltage[:, 1] - reproduced_voltage[:, 1]) ** 2))

    assert rms < threshold
