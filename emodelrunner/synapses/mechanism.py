"""Synapse Point Process Mechanisms."""
# pylint: disable=super-with-arguments
import bluepyopt.ephys as ephys

from emodelrunner.synapses.glusynapse import GluSynapseCustom
from emodelrunner.synapses.synapse import SynapseCustom


class NrnMODPointProcessMechanismCustom(ephys.mechanisms.Mechanism):
    """Class containing all the synapses."""

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
            synapses_data (dict) : synapse data
            synconf_dict (dict) : synapse configuration
            seed (int) : random seed number
            rng_settings_mode (str) : mode of the random number generator
            pre_mtypes (list of ints): activate only synapses whose pre_mtype
                is in this list if None, all synapses are activated
            stim_params (dict or None): dict with pre_mtype as key,
                and netstim params list as item.
                netstim params list is [start, interval, number, noise]
            comment (str) : comment
            use_glu_synapse (bool): if True, instantiate synapses to use GluSynapse
            syn_setup_params (dict): contains extra parameters to setup synapses
                when using GluSynapse
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
        """Returns the cell section on which is the synapse."""
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
        """Instantiate the synapses."""
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
        """Destroy mechanism instantiation."""
        # pylint: disable=unused-argument
        self.pprocesses = None
