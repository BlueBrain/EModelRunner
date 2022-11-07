"""Unit tests for configuration.py."""

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
import pytest
from schema import SchemaError

from tests.utils import cwd
from emodelrunner.configuration import (
    ConfigValidator,
    SSCXConfigValidator,
    SynplasConfigValidator,
    ThalamusConfigValidator,
    PackageType,
    get_validated_config,
)
from emodelrunner.configuration.validator import determine_package_type

sscx_sample_dir = Path("examples") / "sscx_sample_dir"
synplas_sample_dir = Path("examples") / "synplas_sample_dir"
thalamus_sample_dir = Path("examples") / "thalamus_sample_dir"


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
        config_path = Path(".") / "config" / "config_1Hz_10ms.ini"
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
            conf_obj = SSCXConfigValidator().validate_from_file(config)
            assert conf_obj.package_type == PackageType.sscx


def test_valid_synplas_config():
    """Test the validity of the example Synplas configs."""
    with cwd(synplas_sample_dir):
        configs_dir = Path("config")
        configs = list(configs_dir.glob("*.ini"))
        for config in configs:
            conf_obj = SynplasConfigValidator().validate_from_file(config)
            assert conf_obj.package_type == PackageType.synplas


def test_valid_thalamus_config():
    """Test the validity of the example Thalamus configs."""
    with cwd(thalamus_sample_dir):
        configs_dir = Path("config")
        configs = list(configs_dir.glob("*.ini"))
        for config in configs:
            conf_obj = ThalamusConfigValidator().validate_from_file(config)
            assert conf_obj.package_type == PackageType.thalamus


def test_get_validated_config():
    """Test the get_validated_config function."""
    with cwd(sscx_sample_dir):
        config_path = Path(".") / "config" / "config_allsteps.ini"
        conf_obj = get_validated_config(config_path)
        assert conf_obj.package_type == PackageType.sscx

    invalid_conf = Path("tests") / "static_files" / "invalid_config.ini"
    with pytest.raises(ValueError):
        get_validated_config(invalid_conf)


def test_determine_package_type():
    """Test the determine_package_type function."""
    with cwd(sscx_sample_dir):
        config_path = Path(".") / "config" / "config_allsteps.ini"
        assert determine_package_type(config_path) == "sscx"

    with cwd(synplas_sample_dir):
        config_path = Path(".") / "config" / "config_1Hz_10ms.ini"
        assert determine_package_type(config_path) == "synplas"


def test_syn_mech_args_getattribute():
    """Test the __getattribute__ dunder method of SynMechArgs."""
    with cwd(sscx_sample_dir):
        config_path = Path(".") / "config" / "config_allsteps.ini"
        config = get_validated_config(config_path)
    syn_mech_args = config.syn_mech_args()
    assert not syn_mech_args.add_synapses
    with pytest.raises(AttributeError):
        _ = syn_mech_args.seed

    syn_mech_args = config.syn_mech_args(add_synapses=True)
    _ = syn_mech_args.seed
