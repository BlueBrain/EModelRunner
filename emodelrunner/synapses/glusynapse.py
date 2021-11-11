"""GluSynapse class."""

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

from emodelrunner.synapses.synapse import SynapseMixin


class GluSynapseCustom(SynapseMixin):
    """Attach a synapse to the simulation.

    Attributes:
        seed (int): random number generator seed number
        rng_settins_mode (str) : mode of the random number generator
            Can be "Random123" or "Compatibility"
        section (neuron section): cell location where the synapse is attached to
        hsynapse (neuron GluSynapse): Glusynapse instantion in simulator
        delay (float): synapse delay
        weight (float): synapse weight
        pre_mtype (int): ID (but not gid) of the presynaptic cell
        start (int/None): force synapse to start firing at given value when using NetStim
        interval (int/None): force synapse to fire at given interval when using NetStim
        number (int/None): force synapse to fire N times when using NetStim
        noise (int/None): force synapse to have given noise when using NetStim
    """

    def __init__(
        self,
        sim,
        icell,
        synapse,
        section,
        seed,
        rng_settings_mode,
        synconf_dict,
        start=None,
        interval=None,
        number=None,
        noise=None,
    ):
        """Constructor.

        Args:
            sim (NrnSimulator): simulator
            icell (Hoc Cell): cell to which attach the synapse
            synapse (dict): synapse data
            section (neuron section): cell location where the synapse is attached to
            seed (int): random number generator seed number
            rng_settings_mode (str): mode of the random number generator
                Can be "Random123" or "Compatibility"
            synconf_dict (dict): synapse configuration
            start (int/None): force synapse to start firing at given value when using NetStim
            interval (int/None): force synapse to fire at given interval when using NetStim
            number (int/None): force synapse to fire N times when using NetStim
            noise (int/None): force synapse to have given noise when using NetStim
        """
        # pylint: disable=too-many-arguments
        self.seed = seed
        self.rng_settings_mode = rng_settings_mode
        self.section = section

        # the synapse is inhibitory
        if synapse["synapse_type"] < 100:
            raise NotImplementedError()
        # the synapse is excitatory
        self.hsynapse = sim.neuron.h.GluSynapse(synapse["seg_x"], sec=self.section)
        self.hsynapse.tau_d_AMPA = synapse["tau_d"]

        self.hsynapse.Use0_TM = abs(synapse["use"])
        self.hsynapse.Dep_TM = abs(synapse["dep"])
        self.hsynapse.Fac_TM = abs(synapse["fac"])

        self.hsynapse.synapseID = synapse["sid"]

        self.hsynapse.Nrrp_TM = synapse["Nrrp"]

        # set random number generator
        self.set_random_nmb_generator(sim, icell, synapse["sid"])

        self.execute_synapse_configuration(synconf_dict, synapse["sid"], sim)

        self.delay = synapse["delay"]
        self.weight = synapse["weight"]

        self.pre_mtype = synapse["pre_mtype"]

        # netstim params if given
        self.start = start
        self.interval = interval
        self.number = number
        self.noise = noise

    # taken from glusynapseutils.simulation.simulator._runconnectedpair_process
    def set_local_params(self, fit_params, extra_params, c_pre=0.0, c_post=0.0):
        """Set local parameters of given synapse.

        Args:
            fit_params (dict): glusynapse parameters from fitting to get threshold values
            extra_params (dict): contains synapse location and synapse extra parameters
            c_pre (float): calcium peak during a single EPSP
            c_post (float): calcium peak during a single bAP
        """
        # Update basic synapse parameters
        for param in extra_params:
            if param == "loc":
                continue
            # Set parameter
            setattr(self.hsynapse, param, extra_params[param])

        # Update other parameters
        if fit_params is not None:
            if (
                all(key in fit_params for key in ["a00", "a01"])
                and extra_params["loc"] == "basal"
            ):
                # Set basal depression threshold
                self.hsynapse.theta_d_GB = (
                    fit_params["a00"] * c_pre + fit_params["a01"] * c_post
                )
            if (
                all(key in fit_params for key in ["a10", "a11"])
                and extra_params["loc"] == "basal"
            ):
                # Set basal potentiation threshold
                self.hsynapse.theta_p_GB = (
                    fit_params["a10"] * c_pre + fit_params["a11"] * c_post
                )
            if (
                all(key in fit_params for key in ["a20", "a21"])
                and extra_params["loc"] == "apical"
            ):
                # Set apical depression threshold
                self.hsynapse.theta_d_GB = (
                    fit_params["a20"] * c_pre + fit_params["a21"] * c_post
                )
            if (
                all(key in fit_params for key in ["a30", "a31"])
                and extra_params["loc"] == "apical"
            ):
                # Set apical potentiation threshold
                self.hsynapse.theta_p_GB = (
                    fit_params["a30"] * c_pre + fit_params["a31"] * c_post
                )

    # taken from glusynapse.simulation.simulator._runconnectedpair_process
    def setup_synapses(self, params):
        """Set local parameters of given synapse from params dict.

        Args:
            params (dict): contains

                - fit_params: glusynapse parameters from fitting to get threshold values
                - syn_extra_params: synapse location and synapse extra parameters
                - c_pre: calcium peak during a single EPSP
                - c_post: calcium peak during a single bAP
                - postgid: ID of the postsynaptic cell
                - invivo: whether to put synapse in 'in vivo' conditions
        """
        syn_id = int(self.hsynapse.synapseID)
        # Set local parameters
        key = str((params["postgid"], syn_id))
        self.set_local_params(
            params["fit_params"],
            params["syn_extra_params"][key],
            params["c_pre"][key],
            params["c_post"][key],
        )
        # Enable in vivo mode (synapse)
        if params["invivo"]:
            self.hsynapse.Use0_TM = 0.15 * self.hsynapse.Use0_TM
            self.hsynapse.Use_d_TM = 0.15 * self.hsynapse.Use_d_TM
            self.hsynapse.Use_p_TM = 0.15 * self.hsynapse.Use_p_TM
