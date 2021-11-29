"""Configuration parsing and validation."""

# Copyright 2020-2021 Blue Brain Project / EPFL

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import pprint
from pathlib import Path
import configparser
from abc import ABC
from ast import literal_eval

from schema import Schema, And, Or

logger = logging.getLogger(__name__)


class ConfigValidator(ABC):
    """Validates the config through a validation schema.

    Schema validation rules usage:
          - int: checks if the value is int.
          - Or("python", "neuron"): allows either "python" or "neuron".
          - And(str, len): string with length > 0
          - Any named function or lambda expression that evaluates to True is valid.
    """

    config_validator_schema = Schema({})
    default_values = {}

    @staticmethod
    def evaluates_to(n, data_type):
        """Checks if the expression n evaluates to the data_type.

        Args:
            n (str): the parameter value to be evaluated
            data_type (type): the datatype e.g. int, float, str, list

        Returns:
            bool: true n evaluates to the input data type, false otherwise.
        """
        return isinstance(literal_eval(n), data_type)

    @classmethod
    def int_expression(cls, n):
        """Check if n evaluates to an int literal.

        Args:
            n (str): the parameter value to be evaluated

        Returns:
            bool: true if the expression n evaluates to int, false otherwise
        """
        return cls.evaluates_to(n, int)

    @classmethod
    def float_or_int_expression(cls, n):
        """Check if n evaluates to a float or an integer literal.

        Args:
            n (str): the parameter value to be evaluated

        Returns:
            bool: true if the expression n evaluates to float, false otherwise
        """
        return cls.evaluates_to(n, float) or cls.evaluates_to(n, int)

    @staticmethod
    def list_of_nonempty_str(list_instance):
        """Check if the input is a list of nonempty strings.

        The list itself can be empty but it cannot contain an empty string.

        Args:
            list_instance (str): a string that evaluates to list.

        Returns:
            bool: true if the expression evaluates to list of non-empty strings.
        """
        list_instance = literal_eval(list_instance)
        return all(isinstance(s, str) and len(s) for s in list_instance)

    @staticmethod
    def boolean_expression(bool_input):
        """Checks if the expression has an expected boolean value.

        configparser.ConfigParser.getboolean() method evaluates this value.

        Args:
            bool_input (str): string containing boolean input.

        Returns:
            bool: True if the input is in the list of expected inputs.
        """
        return bool_input in ["True", "False", "true", "false", "1", "0"]

    def validate_from_file(self, config_path):
        """Validates the config at the given path and returns it.

        Args:
            config_path (str or Path): path to the .ini configuration file.

        Returns:
            configparser.ConfigParser: the validated config.

        Raises:
            FileNotFoundError: if config_path does not exist.
        """
        config = self._get_unvalidated_config(config_path)

        confdict = {
            section: dict(config.items(section)) for section in config.sections()
        }

        validated_conf = self.config_validator_schema.validate(confdict)
        logger.info("The loaded parameters are:")
        logger.info(pprint.pformat(validated_conf))

        logger.info("The config file is valid.")

        return config

    def _get_unvalidated_config(self, config_path):
        """Returns the config at the given path and fill unset values with default values.

        Args:
            config_path (str or Path): path to the .ini configuration file.

        Returns:
            configparser.ConfigParser: the config.

        Raises:
            FileNotFoundError: if config_path does not exist.
        """
        if not Path(config_path).exists():
            raise FileNotFoundError(f"config file at {config_path} is not found.")
        config = configparser.ConfigParser()

        # set defaults
        config.read_dict(self.default_values)

        config.read(config_path)

        return config


class SSCXConfigValidator(ConfigValidator):
    """Validates the SSCX config through a validation schema."""

    default_values = {
        "Cell": {
            "celsius": "34",
            "v_init": "-80",
            "gid": "0",
        },
        "Protocol": {
            # -1 means there is no apical point
            "apical_point_isec": "-1",
        },
        "Morphology": {
            "do_replace_axon": "True",
            # is only used for naming the output files
            "mtype": "",
        },
        "Sim": {
            "cvode_active": "False",
            "dt": "0.025",
        },
        "Synapses": {
            "add_synapses": "False",
            "seed": "846515",
            "rng_settings_mode": "Random123",  # can be "Random123" or "Compatibility"
            # name to use for the hoc synapse template
            "hoc_synapse_template_name": "hoc_synapses",
        },
        "Paths": {
            "memodel_dir": ".",
            "output_dir": "%(memodel_dir)s/python_recordings",
            "params_path": "%(memodel_dir)s/config/params/final.json",
            "units_path": "%(memodel_dir)s/config/features/units.json",
            "templates_dir": "%(memodel_dir)s/templates",
            "cell_template_path": "%(templates_dir)s/cell_template_neurodamus.jinja2",
            "run_hoc_template_path": "%(templates_dir)s/run_hoc.jinja2",
            "createsimulation_template_path": "%(templates_dir)s/createsimulation.jinja2",
            "synapses_template_path": "%(templates_dir)s/synapses.jinja2",
            "main_protocol_template_path": "%(templates_dir)s/main_protocol.jinja2",
            "features_hoc_template_path": "%(templates_dir)s/features.hoc",
            "replace_axon_hoc_path": "%(templates_dir)s/replace_axon_hoc.hoc",
            "syn_dir_for_hoc": "%(memodel_dir)s/synapses",
            "syn_dir": "%(memodel_dir)s/synapses",
            "syn_data_file": "synapses.tsv",
            "syn_conf_file": "synconf.txt",
            "syn_hoc_file": "synapses.hoc",
            "syn_mtype_map": "mtype_map.tsv",
            "simul_hoc_file": "createsimulation.hoc",
            "cell_hoc_file": "cell.hoc",
            "run_hoc_file": "run.hoc",
            "main_protocol_file": "main_protocol.hoc",
            "features_hoc_file": "features.hoc",
        },
    }

    def __init__(self):
        """Define the schema through validation rules."""
        self.config_validator_schema = Schema(
            {
                "Cell": {
                    "celsius": self.float_or_int_expression,
                    "v_init": self.float_or_int_expression,
                    "gid": self.int_expression,
                    "emodel": And(str, len),
                },
                "Protocol": {
                    "apical_point_isec": self.int_expression,
                },
                "Morphology": {
                    "mtype": And(str, len),
                    "do_replace_axon": self.boolean_expression,
                },
                "Sim": {
                    "cvode_active": self.boolean_expression,
                    "dt": self.float_or_int_expression,
                },
                "Synapses": {
                    "add_synapses": self.boolean_expression,
                    "seed": self.int_expression,
                    "rng_settings_mode": Or("Random123", "Compatibility"),
                    "hoc_synapse_template_name": And(str, len),
                },
                "Paths": {
                    "morph_path": lambda n: Path(n).exists(),
                    "prot_path": lambda n: Path(n).exists(),
                    "features_path": lambda n: Path(n).exists(),
                    "unoptimized_params_path": lambda n: Path(n).exists(),
                    "memodel_dir": lambda n: Path(n).exists(),
                    "output_dir": lambda n: Path(n).exists(),
                    "params_path": lambda n: Path(n).exists(),
                    "units_path": lambda n: Path(n).exists(),
                    "templates_dir": lambda n: Path(n).exists(),
                    "cell_template_path": lambda n: Path(n).exists(),
                    "run_hoc_template_path": lambda n: Path(n).exists(),
                    "createsimulation_template_path": lambda n: Path(n).exists(),
                    "synapses_template_path": lambda n: Path(n).exists(),
                    "main_protocol_template_path": lambda n: Path(n).exists(),
                    "features_hoc_template_path": lambda n: Path(n).exists(),
                    "replace_axon_hoc_path": lambda n: Path(n).exists(),
                    "syn_dir_for_hoc": lambda n: Path(n).exists(),
                    "syn_dir": lambda n: Path(n).exists(),
                    "syn_data_file": And(str, len),
                    "syn_conf_file": And(str, len),
                    "syn_hoc_file": And(str, len),
                    "syn_mtype_map": And(str, len),
                    "simul_hoc_file": And(str, len),
                    "cell_hoc_file": And(str, len),
                    "run_hoc_file": And(str, len),
                    "main_protocol_file": And(str, len),
                    "features_hoc_file": And(str, len),
                },
            }
        )


class SynplasConfigValidator(ConfigValidator):
    """Validates the Synplas config through a validation schema."""

    default_values = {
        "Paths": {
            "memodel_dir": ".",
            "params_path": "%(memodel_dir)s/config/params/final.json",
            "templates_dir": "%(memodel_dir)s/templates",
            "synplas_fit_params_path": "%(memodel_dir)s/config/fit_params.json",
            "replace_axon_hoc_path": "%(templates_dir)s/replace_axon_hoc.hoc",
            "syn_dir": "%(memodel_dir)s/synapses",
            "syn_data_file": "synapses.tsv",
            "syn_conf_file": "synconf.txt",
            "synplas_output_path": "%(memodel_dir)s/output.h5",
            "pairsim_output_path": "%(memodel_dir)s/output.h5",
            "pairsim_precell_output_path": "%(memodel_dir)s/output_precell.h5",
            "syn_prop_path": "%(syn_dir)s/synapse_properties.json",
        },
        "Morphology": {
            "do_replace_axon": "True",
        },
        "Synapses": {
            "seed": "846515",
            "rng_settings_mode": "Random123",  # can be "Random123" or "Compatibility"
        },
    }

    def __init__(self):
        """Define the schema through validation rules."""
        self.config_validator_schema = Schema(
            {
                "Cell": {
                    "celsius": self.float_or_int_expression,
                    "v_init": self.float_or_int_expression,
                    "emodel": And(str, len),
                    "precell_emodel": And(str, len),
                    "gid": self.int_expression,
                    "precell_gid": self.int_expression,
                },
                "Morphology": {
                    "do_replace_axon": self.boolean_expression,
                },
                "Paths": {
                    "morph_path": lambda n: Path(n).exists(),
                    "precell_morph_path": lambda n: Path(n).exists(),
                    "unoptimized_params_path": lambda n: Path(n).exists(),
                    "memodel_dir": lambda n: Path(n).exists(),
                    "params_path": lambda n: Path(n).exists(),
                    "precell_unoptimized_params_path": lambda n: Path(n).exists(),
                    "synplas_fit_params_path": lambda n: Path(n).exists(),
                    "templates_dir": lambda n: Path(n).exists(),
                    "replace_axon_hoc_path": lambda n: Path(n).exists(),
                    "syn_dir": lambda n: Path(n).exists(),
                    "syn_data_file": And(str, len),
                    "syn_conf_file": And(str, len),
                    "stimuli_path": lambda n: Path(n).exists(),
                    "spiketrain_path": lambda n: Path(n).exists(),
                    "syn_prop_path": lambda n: Path(n).exists(),
                    # cannot validate output paths before the files are created,
                    # so check that it is a str
                    "synplas_output_path": And(str, len),
                    "pairsim_output_path": And(str, len),
                    "pairsim_precell_output_path": And(str, len),
                },
                "Protocol": {
                    "tstop": self.float_or_int_expression,
                    "precell_amplitude": self.float_or_int_expression,
                    "precell_width": self.float_or_int_expression,
                    "precell_spikedelay": self.float_or_int_expression,
                },
                "Synapses": {
                    "seed": self.int_expression,
                    "rng_settings_mode": Or("Random123", "Compatibility"),
                },
                "SynapsePlasticity": {
                    "fastforward": self.float_or_int_expression,
                    "invivo": self.boolean_expression,
                    "base_seed": self.int_expression,
                    "synrec": self.list_of_nonempty_str,
                },
            }
        )
