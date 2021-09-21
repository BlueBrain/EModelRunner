"""Custom synapse-related classes."""


class SynapseMixin:
    """Class containing the synapse-related methods."""

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
        # pylint: disable=consider-using-f-string
        for cmd, ids in synconf_dict.items():
            if synapse["sid"] in ids and (exec_all or "*" not in cmd):
                cmd = cmd.replace("%s", "\n%(syn)s")
                hoc_cmd = cmd % {"syn": self.hsynapse.hname()}
                hoc_cmd = "{%s}" % hoc_cmd
                sim.neuron.h(hoc_cmd)


class SynapseCustom(SynapseMixin):
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
            self.hsynapse = sim.neuron.h.ProbGABAAB_EMS(
                synapse["seg_x"], sec=self.section
            )
            self.hsynapse.tau_d_GABAA = synapse["tau_d"]

            self.set_tau_r(sim, icell, synapse)

        # the synapse is excitatory
        elif synapse["synapse_type"] > 100:
            self.hsynapse = sim.neuron.h.ProbAMPANMDA_EMS(
                synapse["seg_x"], sec=self.section
            )
            self.hsynapse.tau_d_AMPA = synapse["tau_d"]

        self.hsynapse.Use = abs(synapse["use"])
        self.hsynapse.Dep = abs(synapse["dep"])
        self.hsynapse.Fac = abs(synapse["fac"])

        self.hsynapse.synapseID = synapse["sid"]

        self.hsynapse.Nrrp = synapse["Nrrp"]

        # set random number generator
        self.set_random_nmb_generator(sim, icell, synapse)

        self.execute_synapse_configuration(synconf_dict, synapse, sim)

        self.delay = synapse["delay"]
        self.weight = synapse["weight"]

        self.pre_mtype = synapse["pre_mtype"]

        # netstim params if given
        self.start = start
        self.interval = interval
        self.number = number
        self.noise = noise
