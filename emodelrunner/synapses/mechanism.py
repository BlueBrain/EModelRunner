"""Synapse Point Process Mechanisms."""

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

from bluepyopt import ephys

from emodelrunner.synapses.glusynapse import GluSynapseCustom
from emodelrunner.synapses.synapse import SynapseCustom


class NrnMODPointProcessMechanismCustom(ephys.mechanisms.Mechanism):
    """Class containing all the synapses.

    Attributes:
        synapses_data (list of dicts): synapse data
        synconf_dict (dict): synapse configuration
        seed (int): random number generator seed number
        rng_settings_mode (str): mode of the random number generator
                Can be "Random123" or "Compatibility"
        pre_mtypes (list of ints): activate only synapses whose pre_mtype
            is in this list if None, all synapses are activated
        stim_params (dict or None): dict with pre_mtype as key,
            and netstim params list as item.
            netstim params list is [start, interval, number, noise]
        use_glu_synapse (bool): if True, instantiate synapses to use GluSynapse
        syn_setup_params (dict): contains extra parameters to setup synapses
            when using GluSynapseCustom
        rng (neuron Random): random number generator of the simulator
        pprocesses (list of SynapseCustom or GluSynapseCustom): list of the synapses
    """

    def __init__(
        self,
        name,
        synapses_data,
        synconf_dict,
        seed,
        rng_settings_mode,
        pre_mtypes=None,
        stim_params=None,
        comment="",
        use_glu_synapse=False,
        syn_setup_params=None,
    ):
        """Constructor.

        Args:
            name (str): name of this object
            synapses_data (list of dicts): synapse data
            synconf_dict (dict): synapse configuration
            seed (int): random number generator seed number
            rng_settings_mode (str): mode of the random number generator
                 Can be "Random123" or "Compatibility"
            pre_mtypes (list of ints): activate only synapses whose pre_mtype
                is in this list if None, all synapses are activated
            stim_params (dict or None): dict with pre_mtype as key,
                and netstim params list as item.
                netstim params list is [start, interval, number, noise]
            comment (str): comment
            use_glu_synapse (bool): if True, instantiate synapses to use GluSynapse
            syn_setup_params (dict): contains extra parameters to setup synapses
                when using GluSynapseCustom
        """
        # pylint: disable=too-many-arguments
        super(NrnMODPointProcessMechanismCustom, self).__init__(name, comment)
        self.synapses_data = synapses_data
        self.synconf_dict = synconf_dict
        self.seed = seed
        self.rng_settings_mode = rng_settings_mode
        self.pre_mtypes = pre_mtypes
        self.stim_params = stim_params
        self.use_glu_synapse = use_glu_synapse
        self.syn_setup_params = syn_setup_params
        self.rng = None
        self.pprocesses = None

    @staticmethod
    def get_cell_section_for_synapse(synapse, icell):
        """Returns the cell section on which is the synapse.

        Args:
            synapse (dict): contains the synapse data
            icell (neuron cell): cell instantiation in simulator

        Returns:
            neuron section where the synapse is attached
        """
        if synapse["sectionlist_id"] == 0:
            section = icell.soma[synapse["sectionlist_index"]]
        elif synapse["sectionlist_id"] == 1:
            section = icell.dend[synapse["sectionlist_index"]]
        elif synapse["sectionlist_id"] == 2:
            section = icell.apic[synapse["sectionlist_index"]]
        elif synapse["sectionlist_id"] == 3:
            section = icell.axon[synapse["sectionlist_index"]]

        return section

    def instantiate(self, sim=None, icell=None):
        """Instantiate the synapses.

        In the process, fill the self.pprocesses list.

        Args:
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            icell (neuron cell): cell instantiation in simulator
        """
        if self.rng_settings_mode == "Random123":
            self.rng = sim.neuron.h.Random()
            self.rng.Random123_globalindex(self.seed)

        self.pprocesses = []
        for synapse in self.synapses_data:
            if self.pre_mtypes is None or synapse["pre_mtype"] in self.pre_mtypes:
                # get section
                section = self.get_cell_section_for_synapse(synapse, icell)

                if self.use_glu_synapse:
                    synapse_obj = GluSynapseCustom(
                        sim,
                        icell,
                        synapse,
                        section,
                        self.seed,
                        self.rng_settings_mode,
                        self.synconf_dict,
                    )
                elif self.stim_params is None:
                    synapse_obj = SynapseCustom(
                        sim,
                        icell,
                        synapse,
                        section,
                        self.seed,
                        self.rng_settings_mode,
                        self.synconf_dict,
                    )
                else:
                    stim_params = self.stim_params[synapse["pre_mtype"]]
                    synapse_obj = SynapseCustom(
                        sim,
                        icell,
                        synapse,
                        section,
                        self.seed,
                        self.rng_settings_mode,
                        self.synconf_dict,
                        stim_params[0],  # start
                        stim_params[1],  # interval
                        stim_params[2],  # number
                        stim_params[3],  # noise
                    )

                # setup synapses params for glu synapse case
                if self.use_glu_synapse and self.syn_setup_params is not None:
                    synapse_obj.setup_synapses(self.syn_setup_params)

                self.pprocesses.append(synapse_obj)

    def destroy(self, sim=None):
        """Destroy mechanism instantiation.

        Args:
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
        """
        # pylint: disable=unused-argument
        self.pprocesses = None
