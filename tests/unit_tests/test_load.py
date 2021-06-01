"""Unit tests for the load.py."""
import pytest
from emodelrunner.load import load_config

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError  # python2.7 case


def test_load_config():
    """Test the config loader."""
    config_file = "config_that_does_not_exist.ini"
    with pytest.raises(FileNotFoundError):
        load_config(config_dir="config", filename=config_file)