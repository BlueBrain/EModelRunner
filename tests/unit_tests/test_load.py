"""Unit tests for the load.py."""
import pytest
from emodelrunner.load import load_config


def test_load_config():
    """Test the config loader."""
    config_path = "config/config_that_does_not_exist.ini"
    with pytest.raises(FileNotFoundError):
        load_config(config_path=config_path)
