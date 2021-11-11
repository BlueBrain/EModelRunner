"""Spontaneous Minis."""

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


# adapted from bglibpy.cell.add_replay_minis
class Minis(ephys.stimuli.Stimulus):
    """Current stimulus based on stochastic current amplitude."""

    def __init__(
        self,
        gid,
        locations=None,
        stop=None,
        minis_seed=0,
        base_seed=0,
        weight_scalar=None,
        syn_location=None,
        popids=None,
        spont_minis_rate=None,
    ):
        """Constructor."""
        # pylint: disable=too-many-arguments
        super(Minis, self).__init__()
        self.gid = gid
        if stop is None:
            raise ValueError("NrnVecStimStimulus: Need to specify a stop time")
        # must be named total_duration because of ephys.protocols
        self.total_duration = stop

        self.locations = locations

        self.minis_seed = minis_seed
        self.base_seed = base_seed
        self.weight_scalar = weight_scalar
        self.syn_location = syn_location
        self.popids = popids
        self.spont_minis_rate = spont_minis_rate
        self.persistent = []
        self.ips = {}
        self.syn_mini_netcons = {}

    def instantiate(self, sim=None, icell=None):
        """Run stimulus."""
        # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        # pylint: disable=consider-using-f-string
        if self.persistent is None:
            self.persistent = []
        if self.ips is None:
            self.ips = {}
        if self.syn_mini_netcons is None:
            self.syn_mini_netcons = {}

        for location in self.locations:
            # self.connections[location.name] = []
            for synapse in location.instantiate(sim=sim, icell=icell):

                sid = synapse.hsynapse.synapseID

                if self.popids is None:
                    # Default values in Neurodamus
                    source_popid = 0
                    target_popid = 0
                else:
                    source_popid, target_popid = self.popids[sid]

                if self.weight_scalar is not None and sid in self.weight_scalar:
                    weight_scalar = self.weight_scalar[sid]
                else:
                    weight_scalar = 1.0

                if self.spont_minis_rate is not None and sid in self.spont_minis_rate:
                    spont_minis_rate = self.spont_minis_rate[sid]
                else:
                    spont_minis_rate = None

                if spont_minis_rate is not None:
                    # add the *minis*: spontaneous synaptic events
                    self.ips[sid] = sim.neuron.h.InhPoissonStim(
                        self.syn_location[sid], sec=synapse.section  # load this
                    )

                    delay = 0.1
                    self.syn_mini_netcons[sid] = sim.neuron.h.NetCon(
                        self.ips[sid],
                        synapse.hsynapse,
                        -30,
                        delay,
                        synapse.weight * weight_scalar,
                    )
                    # set netcon type
                    nc_param_name = "nc_type_param_{}".format(synapse.hsynapse).split(
                        "[", maxsplit=1
                    )[0]
                    if hasattr(sim.neuron.h, nc_param_name):
                        nc_type_param = int(getattr(sim.neuron.h, nc_param_name))
                        # NC_SPONTMINI
                        self.syn_mini_netcons[sid].weight[nc_type_param] = 1

                    # I assumed rng_settings_mode is the same as in synapse
                    if synapse.rng_settings_mode == "Random123":
                        seed2 = source_popid * 65536 + target_popid + self.minis_seed
                        self.ips[sid].setRNGs(
                            sid + 200,
                            self.gid + 250,
                            seed2 + 300,
                            sid + 200,
                            self.gid + 250,
                            seed2 + 350,
                        )
                    else:
                        exprng = sim.neuron.h.Random()
                        self.persistent.append(exprng)

                        uniformrng = sim.neuron.h.Random()
                        self.persistent.append(uniformrng)

                        if synapse.rng_settings_mode == "Compatibility":
                            exp_seed1 = sid * 100000 + 200
                            exp_seed2 = (
                                self.gid + 250 + self.base_seed + self.minis_seed
                            )
                            uniform_seed1 = sid * 100000 + 300
                            uniform_seed2 = (
                                self.gid + 250 + self.base_seed + self.minis_seed
                            )
                        elif synapse.rng_settings_mode == "UpdatedMCell":
                            exp_seed1 = sid * 1000 + 200
                            exp_seed2 = (
                                source_popid * 16777216
                                + self.gid
                                + 250
                                + self.base_seed
                                + self.minis_seed
                            )
                            uniform_seed1 = sid * 1000 + 300
                            uniform_seed2 = (
                                source_popid * 16777216
                                + self.gid
                                + 250
                                + self.base_seed
                                + self.minis_seed
                            )
                        else:
                            raise ValueError(
                                f"Cell: Unknown rng mode: {synapse.rng_settings_mode}"
                            )

                        exprng.MCellRan4(exp_seed1, exp_seed2)
                        exprng.negexp(1.0)

                        uniformrng.MCellRan4(uniform_seed1, uniform_seed2)
                        uniformrng.uniform(0.0, 1.0)

                        self.ips[sid].setRNGs(exprng, uniformrng)

                    tbins_vec = sim.neuron.h.Vector(1)
                    tbins_vec.x[0] = 0.0
                    rate_vec = sim.neuron.h.Vector(1)
                    rate_vec.x[0] = spont_minis_rate
                    self.persistent.append(tbins_vec)
                    self.persistent.append(rate_vec)
                    self.ips[sid].setTbins(tbins_vec)
                    self.ips[sid].setRate(rate_vec)

    def destroy(self, sim=None):
        """Destroy stimulus."""
        # pylint: disable=unused-argument
        self.persistent = None
        self.ips = None
        self.syn_mini_netcons = None

    def __str__(self):
        """String representation."""
        # pylint: disable=consider-using-f-string
        return (
            "Minis at %s" % ",".join(location for location in self.locations)
            if self.locations is not None
            else "Minis"
        )
