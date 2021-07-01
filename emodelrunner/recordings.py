"""Custom Recording class."""

import logging

from bluepyopt import ephys

logger = logging.getLogger(__name__)


class RecordingCustom(ephys.recordings.CompRecording):
    """Response to stimulus with recording every 0.1 ms."""

    def __init__(self, name=None, location=None, variable="v"):
        """Constructor.

        Args:
            name (str): name of this object
            location (Location): location in the model of the recording
            variable (str): which variable to record from (e.g. 'v')
        """
        super(RecordingCustom, self).__init__(
            name=name, location=location, variable=variable
        )

    def instantiate(self, sim=None, icell=None):
        """Instantiate recording."""
        logger.debug(
            "Adding compartment recording of %s at %s", self.variable, self.location
        )

        self.varvector = sim.neuron.h.Vector()
        seg = self.location.instantiate(sim=sim, icell=icell)
        self.varvector.record(getattr(seg, "_ref_%s" % self.variable), 0.1)

        self.tvector = sim.neuron.h.Vector()
        self.tvector.record(sim.neuron.h._ref_t, 0.1)  # pylint: disable=W0212

        self.instantiated = True


class SynapseRecordingCustom(ephys.recordings.Recording):
    """Recording in synaptic locations."""

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
        """Return recording response."""
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
        """Instantiate recording."""
        logger.debug(
            "Adding compartment recording of %s at %s", self.variable, self.location
        )

        pprocesses = self.location.instantiate(sim=sim, icell=icell)
        for synapse in pprocesses:
            varvector = sim.neuron.h.Vector()
            varvector.record(getattr(synapse.hsynapse, "_ref_%s" % self.variable))
            self.varvectors.append(varvector)

        self.tvector = sim.neuron.h.Vector()
        self.tvector.record(sim.neuron.h._ref_t)  # pylint: disable=W0212

        self.instantiated = True

    def destroy(self, sim=None):
        """Destroy recording."""
        # pylint: disable=unused-argument
        self.varvectors = None
        self.tvector = None
        self.instantiated = False

    def __str__(self):
        """String representation."""
        return "%s: %s at %s" % (self.name, self.variable, self.location)
