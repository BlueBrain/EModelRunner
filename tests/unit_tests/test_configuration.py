"""Unit tests for configuration.py."""

from pathlib import Path
import pytest
from schema import SchemaError

from tests.utils import cwd
from emodelrunner.configuration import (
    ConfigValidator,
    SSCXConfigValidator,
    SynplasConfigValidator,
)

sscx_sample_dir = Path("examples") / "sscx_sample_dir"
synplas_sample_dir = Path("examples") / "synplas_sample_dir"


def test_evaluates_to():
    """Test to check literals evaluate correctly."""
    assert ConfigValidator.evaluates_to("[1,2,3]", list)
    assert ConfigValidator.evaluates_to("'loremipsum'", str)
    assert ConfigValidator.evaluates_to("55", int)
    assert ConfigValidator.evaluates_to("55.0", float)
    assert not ConfigValidator.evaluates_to("55.0", int)
    assert not ConfigValidator.evaluates_to("55", float)


def test_int_expression():
    """Test to check integer literals evaluate correctly."""
    assert ConfigValidator.int_expression("0")
    assert ConfigValidator.int_expression("10")
    assert not ConfigValidator.int_expression("10.1")


def test_float_expression():
    """Test to check float literals evaluate correctly."""
    assert ConfigValidator.float_or_int_expression("0.0")
    assert ConfigValidator.float_or_int_expression("10.0")
    assert ConfigValidator.float_or_int_expression("10")


def test_list_of_nonempty_str():
    """Test to check lists of non-empty string evaluate correctly."""
    assert ConfigValidator.list_of_nonempty_str('["bNAC", "dSTUT"]')
    assert not ConfigValidator.list_of_nonempty_str('["bNAC", "dSTUT", ""]')
    assert ConfigValidator.list_of_nonempty_str("[]")
    assert not ConfigValidator.list_of_nonempty_str('[""]')


def test_missing_config():
    """Test the config loader."""
    config_path = Path("config") / "config_that_does_not_exist.ini"
    with pytest.raises(FileNotFoundError):
        SSCXConfigValidator().validate_from_file(config_path)


def test_invalid_sscx_config():
    """Runs validator with an invalid SSCX config that raises a SchemaError."""
    with cwd(synplas_sample_dir):
        config_path = Path(".") / "config" / "config_pairsim.ini"
        conf_validator = SSCXConfigValidator()
        with pytest.raises(SchemaError):
            _ = conf_validator.validate_from_file(config_path)


def test_invalid_synplas_config():
    """Runs validator with an invalid Synplas config that raises a SchemaError."""
    with cwd(sscx_sample_dir):
        config_path = Path(".") / "config" / "config_allsteps.ini"
        conf_validator = SynplasConfigValidator()
        with pytest.raises(SchemaError):
            _ = conf_validator.validate_from_file(config_path)


def test_valid_sscx_config():
    """Test the validity of the example SSCX configs."""

    with cwd(sscx_sample_dir):
        configs_dir = Path("config")
        configs = list(configs_dir.glob("*.ini"))
        for config in configs:
            SSCXConfigValidator().validate_from_file(config)


def test_valid_synplas_config():
    """Test the validity of the example Synplas configs."""

    with cwd(synplas_sample_dir):
        configs_dir = Path("config")
        configs = list(configs_dir.glob("*.ini"))
        for config in configs:
            SynplasConfigValidator().validate_from_file(config)
