"""Custom synapse-related classes."""

# pylint: disable=super-with-arguments, unused-argument, too-many-arguments
import random
import bluepyopt.ephys as ephys


class SynapseCustom:
    """Attach a synapse to the simulation."""

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
            synapse (dict) : synapse data
            section (): cell location where the synapse is attached to
            seed (int) : random seed number
            rng_settings_mode (str) : mode of the random number generator
            synconf_dict (dict) : synapse configuration
            start (int/None): force synapse to start firing at given value
            interval (int/None): force synapse to fire at given interval
            number (int/None): force synapse to fire N times
            noise (int/None): force synapse to have given noise
        """
        self.seed = seed
        self.rng_settings_mode = rng_settings_mode

        # the synapse is inhibitory
        if synapse["synapse_type"] < 100:
            self.hsynapse = sim.neuron.h.ProbGABAAB_EMS(synapse["seg_x"], sec=section)
            self.hsynapse.tau_d_GABAA = synapse["tau_d"]

            self.set_tau_r(sim, icell, synapse)

        # the synapse is excitatory
        elif synapse["synapse_type"] > 100:
            self.hsynapse = sim.neuron.h.ProbAMPANMDA_EMS(synapse["seg_x"], sec=section)
            self.hsynapse.tau_d_AMPA = synapse["tau_d"]

        self.hsynapse.Use = abs(synapse["use"])
        self.hsynapse.Dep = abs(synapse["dep"])
        self.hsynapse.Fac = abs(synapse["fac"])

        # set random number generator
        self.set_random_nmb_generator(sim, icell, synapse)

        self.hsynapse.synapseID = synapse["sid"]

        self.hsynapse.Nrrp = synapse["Nrrp"]

        self.execute_synapse_configuration(synconf_dict, synapse, sim)

        self.delay = synapse["delay"]
        self.weight = synapse["weight"]

        self.pre_mtype = synapse["pre_mtype"]

        # netstim params if given
        self.start = start
        self.interval = interval
        self.number = number
        self.noise = noise

    def set_random_nmb_generator(self, sim, icell, synapse):
        """Sets the random number generator."""
        if self.rng_settings_mode == "Random123":
            self.randseed1 = icell.gid + 250
            self.randseed2 = synapse["sid"] + 100
            self.randseed3 = 300

            self.hsynapse.setRNG(self.randseed1, self.randseed2, self.randseed3)

        if self.rng_settings_mode == "Compatibility":
            self.rndd = sim.neuron.h.Random()
            self.rndd.MCellRan4(
                synapse["sid"] * 100000 + 100,
                icell.gid + 250 + self.seed,
            )
            self.rndd.uniform(0, 1)

            self.hsynapse.setRNG(self.rndd)

    def set_tau_r(self, sim, icell, synapse):
        """Set tau_r_GABAA using random nmb generator."""
        self.rng = sim.neuron.h.Random()
        if self.rng_settings_mode == "Random123":
            self.rng.Random123(icell.gid + 250, synapse["sid"] + 100, 450)
        elif self.rng_settings_mode == "Compatibility":
            self.rng.MCellRan4(
                synapse["sid"] * 100000 + 100,
                icell.gid + 250 + self.seed,
            )
        self.rng.lognormal(0.2, 0.1)
        self.hsynapse.tau_r_GABAA = self.rng.repick()

    def execute_synapse_configuration(self, synconf_dict, synapse, sim, exec_all=False):
        """Create a hoc file configuring synapse."""
        for cmd, ids in synconf_dict.items():
            if synapse["sid"] in ids and (exec_all or "*" not in cmd):
                cmd = cmd.replace("%s", "\n%(syn)s")
                hoc_cmd = cmd % {"syn": self.hsynapse.hname()}
                hoc_cmd = "{%s}" % hoc_cmd
                sim.neuron.h(hoc_cmd)


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
    ):
        """Constructor.

        Args:
            name (str): name of this object
            synapses_data (dict) : synapse data
            synconf_dict (dict) : synapse configuration
            seed (int) : random seed number
            rng_settings_mode (str) : mode of the random number generator
            pre_mtypes (list of ints): activate only synapses whose pre_mtype is in this list
                if None, all synapses are activated
            stim_params (dict or None): dict with pre_mtype as key, and netstim params list as item
                netstim params list is [start, interval, number, noise]
            comment (str) : comment
        """
        super(NrnMODPointProcessMechanismCustom, self).__init__(name, comment)
        self.synapses_data = synapses_data
        self.synconf_dict = synconf_dict
        self.seed = seed
        self.rng_settings_mode = rng_settings_mode
        self.pre_mtypes = pre_mtypes
        self.stim_params = stim_params
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

                if self.stim_params is None:
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

                self.pprocesses.append(synapse_obj)

    def destroy(self, sim=None):
        """Destroy mechanism instantiation."""
        self.pprocesses = None


class NrnNetStimStimulusCustom(ephys.stimuli.Stimulus):
    """Current stimulus based on current amplitude and time series."""

    def __init__(
        self,
        locations=None,
        total_duration=None,
        interval=None,
        number=None,
        start=None,
        noise=0,
    ):
        """Constructor.

        Args:
            locations: synapse point process location to connect to
            total_duration: duration of run (ms)
            interval: time between spikes (ms)
            number: average number of spikes
            start: most likely start time of first spike (ms)
            noise: fractional randomness (0 deterministic,
                   1 negexp interval distrubtion)
        """
        super(NrnNetStimStimulusCustom, self).__init__()
        if total_duration is None:
            raise ValueError("NrnNetStimStimulus: Need to specify a total duration")
        self.total_duration = total_duration

        self.locations = locations
        self.interval = interval
        self.number = number
        self.start = start
        self.noise = noise
        self.connections = {}

    def instantiate(self, sim=None, icell=None):
        """Run stimulus."""
        if self.connections is None:
            self.connections = {}
        for location in self.locations:
            self.connections[location.name] = []
            for synapse in location.instantiate(sim=sim, icell=icell):
                netstim = sim.neuron.h.NetStim()
                netstim.interval = (
                    synapse.interval if synapse.interval is not None else self.interval
                )
                netstim.number = (
                    synapse.number if synapse.number is not None else self.number
                )
                netstim.start = (
                    synapse.start if synapse.start is not None else self.start
                )
                netstim.noise = (
                    synapse.noise if synapse.noise is not None else self.noise
                )
                netcon = sim.neuron.h.NetCon(
                    netstim, synapse.hsynapse, -30, synapse.delay, synapse.weight
                )

                self.connections[location.name].append((netcon, netstim))

    def destroy(self, sim=None):
        """Destroy stimulus."""
        self.connections = None

    def __str__(self):
        """String representation."""
        return (
            "Netstim at %s" % ",".join(location for location in self.locations)
            if self.locations is not None
            else "Netstim"
        )


class NrnVecStimStimulusCustom(ephys.stimuli.Stimulus):
    """Current stimulus based on stochastic current amplitude."""

    def __init__(
        self,
        locations=None,
        start=None,
        stop=None,
        seed=1,
        vecstim_random="python",
    ):
        """Constructor.

        Args:
            locations: synapse point process location to connect to
            start: most likely start time of first spike (ms)
            stop: time after which no synapses are allowed to fire (ms)
            seed: seed for random number generator
            vecstim_random: origin of the random nmb gener. for vecstim. can be python or neuron
        """
        super(NrnVecStimStimulusCustom, self).__init__()
        if stop is None:
            raise ValueError("NrnVecStimStimulus: Need to specify a stop time")
        # must be named total_duration because of ephys.protocols
        self.total_duration = stop

        self.locations = locations
        self.start = start
        self.seed = seed
        self.vecstim_random = vecstim_random
        self.connections = {}

    def instantiate(self, sim=None, icell=None):
        """Run stimulus."""
        if self.connections is None:
            self.connections = {}

        if self.vecstim_random == "python":
            random.seed(self.seed)
        else:
            rand = sim.neuron.h.Random(self.seed)
            rand.uniform(self.start, self.total_duration)

        for location in self.locations:
            self.connections[location.name] = []
            for synapse in location.instantiate(sim=sim, icell=icell):
                if self.vecstim_random == "python":
                    spike_train = [random.uniform(self.start, self.total_duration)]
                else:
                    spike_train = [rand.repick()]

                t_vec = sim.neuron.h.Vector(spike_train)
                vecstim = sim.neuron.h.VecStim()
                vecstim.play(t_vec, sim.dt)
                netcon = sim.neuron.h.NetCon(
                    vecstim, synapse.hsynapse, -30, synapse.delay, synapse.weight
                )

                self.connections[location.name].append((netcon, vecstim, t_vec))

    def destroy(self, sim=None):
        """Destroy stimulus."""
        self.connections = None

    def __str__(self):
        """String representation."""
        return (
            "Vecstim at %s" % ",".join(location for location in self.locations)
            if self.locations is not None
            else "Vecstim"
        )
