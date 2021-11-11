"""Custom Recording class."""

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

from bluepyopt import ephys

logger = logging.getLogger(__name__)


class SynapseRecordingCustom(ephys.recordings.Recording):
    """Recording in synaptic locations.

    Attributes:
        name (str): name of this object
        location (Location): location in the model of the recording
        variable (str): which variable to record from (e.g. 'v')
        varvectors (list of neuron Vector): vectors recording the variable
        tvector (neuron Vector): vector recording the time (ms)
        instantiated (bool): whether the object has been instantiated or not
    """

    def __init__(self, name=None, location=None, variable="v"):
        """Constructor.

        Args:
            name (str): name of this object
            location (Location): location in the model of the recording
            variable (str): which variable to record from (e.g. 'v')
        """
        super(SynapseRecordingCustom, self).__init__(name=name)
        self.location = location
        self.variable = variable

        self.varvectors = []
        self.tvector = None

        self.instantiated = False

    @property
    def response(self):
        """Return recording responses.

        Returns:
            list of recorded responses
        """
        if not self.instantiated:
            return None

        responses = []
        for varvector in self.varvectors:
            responses.append(
                ephys.recordings.responses.TimeVoltageResponse(
                    self.name, self.tvector.to_python(), varvector.to_python()
                )
            )

        return responses

    def instantiate(self, sim=None, icell=None):
        """Instantiate recording.

        Args:
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            icell (neuron cell): cell instantiation in simulator
        """
        logger.debug(
            "Adding compartment recording of %s at %s", self.variable, self.location
        )

        pprocesses = self.location.instantiate(sim=sim, icell=icell)
        for synapse in pprocesses:
            varvector = sim.neuron.h.Vector()
            varvector.record(getattr(synapse.hsynapse, f"_ref_{self.variable}"))
            self.varvectors.append(varvector)

        self.tvector = sim.neuron.h.Vector()
        self.tvector.record(sim.neuron.h._ref_t)  # pylint: disable=W0212

        self.instantiated = True

    def destroy(self, sim=None):
        """Destroy recording.

        Args:
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
        """
        # pylint: disable=unused-argument
        self.varvectors = None
        self.tvector = None
        self.instantiated = False

    def __str__(self):
        """String representation.

        Returns:
            string representation
        """
        return f"{self.name}: {self.variable} at {self.location}"
