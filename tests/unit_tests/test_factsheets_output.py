"""Unit tests for the factsheet outputs."""

from pathlib import Path
import json

import pytest

from emodelrunner.factsheets.output import write_etype_factsheet


def test_write_etype_factsheet(tmp_path):
    """Test etype_factsheet creation."""
    current_amplitude = 0.35
    delay = 20
    duration = 70
    voltage_path = (
        Path("tests") / "thalamus_tests" / "data" / "VPL_TC.Step_150.soma.v.dat"
    )

    outfile = tmp_path / "etype.json"

    write_etype_factsheet(voltage_path, current_amplitude, delay, duration, outfile)

    assert outfile.exists()

    with open(outfile, "r") as f:
        etype_data = json.load(f)

    assert etype_data["values"][0]["name"] == "resting membrane potential"
    assert etype_data["values"][0]["value"] == pytest.approx(-61.955815)
    assert etype_data["values"][1]["name"] == "input resistance"
    assert etype_data["values"][1]["value"] == pytest.approx(11.5625477)
    assert etype_data["values"][2]["name"] == "membrane time constant"
    assert etype_data["values"][2]["value"] == pytest.approx(43.9689159)
