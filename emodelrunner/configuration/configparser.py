"""Configuration parsing."""

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


from configparser import ConfigParser
from enum import Enum

from emodelrunner.configuration.subgroups import (
    HocPaths,
    ProtArgs,
    SynMechArgs,
    MorphArgs,
    PresynStimArgs,
)


class PackageType(Enum):
    """Enumerator for the emodel package types."""

    sscx = "sscx"
    thalamus = "thalamus"
    synplas = "synplas"


class EModelConfigParser(ConfigParser):
    """Built-in ConfigParser annotated with package type."""

    def __init__(self):
        """Constructor."""
        super().__init__()

    @property
    def package_type(self):
        """Package type as a property."""
        return PackageType[self.get("Package", "type")]

    def hoc_paths_args(self):
        """Get the config data subgroup containing the paths to the hoc files."""
        return HocPaths(
            hoc_dir=self.get("Paths", "memodel_dir"),
            cell_hoc_filename=self.get("Paths", "cell_hoc_file"),
            simul_hoc_filename=self.get("Paths", "simul_hoc_file"),
            run_hoc_filename=self.get("Paths", "run_hoc_file"),
            syn_dir=self.get("Paths", "syn_dir"),
            syn_dir_for_hoc=self.get("Paths", "syn_dir_for_hoc"),
            syn_hoc_filename=self.get("Paths", "syn_hoc_file"),
            main_protocol_filename=self.get("Paths", "main_protocol_file"),
        )

    def prot_args(self):
        """Get the subgroup containing protocols configuration data."""
        return ProtArgs(
            emodel=self.get("Cell", "emodel"),
            apical_point_isec=self.getint("Protocol", "apical_point_isec"),
            mtype=self.get("Morphology", "mtype"),
            prot_path=self.get("Paths", "prot_path"),
            features_path=self.get("Paths", "features_path"),
        )

    def syn_mech_args(self, add_synapses=None, seed=None, rng_settings_mode=None):
        """Get the data from config used when loading synapse mechanisms."""
        if add_synapses is None:
            add_synapses = self.getboolean("Synapses", "add_synapses")
        if seed is None:
            seed = self.getint("Synapses", "seed")
        if rng_settings_mode is None:
            rng_settings_mode = self.get("Synapses", "rng_settings_mode")

        return SynMechArgs(
            add_synapses=add_synapses,
            seed=seed,
            rng_settings_mode=rng_settings_mode,
            syn_conf_file=self.get("Paths", "syn_conf_file"),
            syn_data_file=self.get("Paths", "syn_data_file"),
            syn_dir=self.get("Paths", "syn_dir"),
        )

    def morph_args(self):
        """Get morphology arguments for SSCX from the configuration object."""
        morph_args = {}
        morph_args["morph_path"] = self.get("Paths", "morph_path")
        morph_args["do_replace_axon"] = self.getboolean("Morphology", "do_replace_axon")

        if self.package_type == PackageType.sscx:
            morph_args["axon_hoc_path"] = self.get("Paths", "replace_axon_hoc_path")

        return MorphArgs(**morph_args)

    def synplas_morph_args(self, precell=False):
        """Get morphology arguments for Synplas from the configuration object.

        Args:
            precell (bool): True to load precell morph. False to load usual morph.
        """
        # load morphology path
        if precell:
            morph_path = self.get("Paths", "precell_morph_path")
        else:
            morph_path = self.get("Paths", "morph_path")

        morph_args = {
            "morph_path": morph_path,
            "do_replace_axon": self.getboolean("Morphology", "do_replace_axon"),
        }
        return MorphArgs(**morph_args)

    def presyn_stim_args(self, pre_spike_train):
        """Get the pre-synaptic stimulus config data.

        Args:
            pre_spike_train (list): times at which the synapses fire (ms)
        """
        # spikedelay is the time between the start of the stimulus
        # and the precell spike time
        spike_delay = self.getfloat("Protocol", "precell_spikedelay")

        # stim train is the times at which to stimulate the precell
        return PresynStimArgs(
            stim_train=pre_spike_train - spike_delay,
            amp=self.getfloat("Protocol", "precell_amplitude"),
            width=self.getfloat("Protocol", "precell_width"),
        )
