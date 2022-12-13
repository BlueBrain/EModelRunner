"""Unit tests for load functions."""

import os
from emodelrunner.load import load_synapse_configuration_data


def test_load_synapse_configuration_data():
    """Unit test for synconf loading function."""
    synconf_path = os.path.join("tests", "data", "synconf.txt")
    synconf = load_synapse_configuration_data(synconf_path)

    assert len(synconf.keys()) == 4
    assert "%s.mg = 1.0" in synconf
    assert len(synconf["%s.Use *= 1.0"]) == 652
    assert "('', 10)" in synconf["%s.NMDA_ratio = 0.8"]
