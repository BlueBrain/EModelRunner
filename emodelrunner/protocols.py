"""Protocol creation functions & custom protocol classes."""
import collections
import logging
import sys
import traceback

import bluepyopt.ephys as ephys

logger = logging.getLogger(__name__)


def fastforward_synapses(cell_model):
    """Enable synapse fast-forwarding."""
    for mech in cell_model.mechanisms:
        if hasattr(mech, "pprocesses"):
            for synapse in mech.pprocesses:
                if synapse.hsynapse.rho_GB >= 0.5:
                    synapse.hsynapse.rho_GB = 1.0
                    synapse.hsynapse.Use_TM = synapse.hsynapse.Use_p_TM
                    synapse.hsynapse.gmax_AMPA = synapse.hsynapse.gmax_p_AMPA
                else:
                    synapse.hsynapse.rho_GB = 0.0
                    synapse.hsynapse.Use_TM = synapse.hsynapse.Use_d_TM
                    synapse.hsynapse.gmax_AMPA = synapse.hsynapse.gmax_d_AMPA


class SweepProtocolCustom(ephys.protocols.SweepProtocol):
    """SweepProtocol with ability of synapse fastforwarding."""

    def __init__(
        self,
        name=None,
        stimuli=None,
        recordings=None,
        cvode_active=None,
        fastforward=None,
    ):
        """Constructor."""
        # pylint: disable=super-with-arguments
        super(SweepProtocolCustom, self).__init__(
            name, stimuli, recordings, cvode_active
        )

        self.fastforward = fastforward

    def _run_func(self, cell_model, param_values, sim=None):
        """Run protocols."""
        # pylint: disable=raise-missing-from
        try:
            cell_model.freeze(param_values)
            cell_model.instantiate(sim=sim)

            self.instantiate(sim=sim, icell=cell_model.icell)

            try:
                if self.fastforward is not None:
                    sim.run(self.fastforward, cvode_active=self.cvode_active)
                    fastforward_synapses(cell_model)
                    sim.neuron.h.cvode_active(1)
                    sim.neuron.h.continuerun(self.total_duration)
                else:
                    sim.run(self.total_duration, cvode_active=self.cvode_active)
            except (RuntimeError, ephys.simulators.NrnSimulatorException):
                logger.debug(
                    "SweepProtocol: Running of parameter set {%s} generated "
                    "an exception, returning None in responses",
                    str(param_values),
                )
                responses = {recording.name: None for recording in self.recordings}
            else:
                responses = {
                    recording.name: recording.response for recording in self.recordings
                }

            self.destroy(sim=sim)

            cell_model.destroy(sim=sim)

            cell_model.unfreeze(param_values.keys())

            return responses
        except BaseException:
            raise Exception("".join(traceback.format_exception(*sys.exc_info())))


class SweepProtocolPairSim(ephys.protocols.Protocol):
    """Sweep protocol for pair simulation with fastforwarding."""

    def __init__(
        self,
        name=None,
        stimuli=None,
        recordings=None,
        cvode_active=None,
        fastforward=None,
    ):
        """Constructor.

        Args:
            name (str): name of this object.
            stimuli (list of 2 lists of Stimuli): Stimulus objects used in the protocol
                The list must be of size 2 and
                contain first the list for the presynaptic stimuli
                and then the list for the postsynaptic stimuli.
            recordings (list of 2 lists of Recordings): Recording objects used in the
                protocol. The list must be of size 2 and
                contain first the list for the presynaptic recording
                and then the list for the postsynaptic recording.
            cvode_active (bool): whether to use variable time step
            fastforward (float): Time after which the synapses are fasforwarded.
                Leave None for no fastforward.
        """
        # pylint: disable=super-with-arguments
        super(SweepProtocolPairSim, self).__init__(name)
        if stimuli is not None and len(stimuli) != 2:
            raise Exception(
                "Stimuli should be of size 2 and contain"
                "[presynaptic_stimuli, postsynaptic_stimuli]"
            )
        self.stimuli = stimuli
        if recordings is not None and len(stimuli) != 2:
            raise Exception(
                "Recordings should be of size 2 and contain"
                "[presynaptic_recordings, postsynaptic_recordings]"
            )
        self.recordings = recordings
        self.cvode_active = cvode_active
        self.fastforward = fastforward

    @property
    def total_duration(self):
        """Total duration."""
        return max(
            [
                stimulus.total_duration
                for stimulus_sublist in self.stimuli
                for stimulus in stimulus_sublist
            ]
        )

    def subprotocols(self):
        """Return subprotocols."""
        return collections.OrderedDict({self.name: self})

    def _run_func(
        self,
        precell_model,
        postcell_model,
        pre_param_values,
        post_param_values,
        sim=None,
    ):
        """Run protocols."""
        # pylint: disable=raise-missing-from
        try:
            precell_model.freeze(pre_param_values)
            precell_model.instantiate(sim=sim)

            postcell_model.freeze(post_param_values)
            postcell_model.instantiate(sim=sim)

            self.instantiate(
                sim=sim, pre_icell=precell_model.icell, post_icell=postcell_model.icell
            )

            try:
                if self.fastforward is not None:
                    sim.run(self.fastforward, cvode_active=self.cvode_active)
                    fastforward_synapses(precell_model)
                    fastforward_synapses(postcell_model)
                    sim.neuron.h.cvode_active(1)
                    sim.neuron.h.continuerun(self.total_duration)
                else:
                    sim.run(self.total_duration, cvode_active=self.cvode_active)
            except (RuntimeError, ephys.simulators.NrnSimulatorException):
                logger.debug(
                    "SweepProtocol: Running of parameter sets {%s} and {%s} generated "
                    "an exception, returning None in responses",
                    str(pre_param_values),
                    str(post_param_values),
                )
                responses = [
                    {recording.name: None for recording in recordings}
                    for recordings in self.recordings
                ]
            else:
                responses = [
                    {recording.name: recording.response for recording in recordings}
                    for recordings in self.recordings
                ]

            self.destroy(sim=sim)

            precell_model.destroy(sim=sim)
            postcell_model.destroy(sim=sim)

            precell_model.unfreeze(pre_param_values.keys())
            postcell_model.unfreeze(post_param_values.keys())

            return responses
        except BaseException:
            raise Exception("".join(traceback.format_exception(*sys.exc_info())))

    def run(
        self,
        precell_model,
        postcell_model,
        pre_param_values,
        post_param_values,
        sim=None,
        isolate=None,
        timeout=None,
    ):
        """Instantiate protocol."""
        # pylint:disable=too-many-locals, import-outside-toplevel
        if isolate is None:
            isolate = True

        if isolate:

            def _reduce_method(meth):
                """Overwrite reduce."""
                return (getattr, (meth.__self__, meth.__func__.__name__))

            import copyreg
            import types

            copyreg.pickle(types.MethodType, _reduce_method)
            import pebble
            from concurrent.futures import TimeoutError as FuturesTimeoutError

            if timeout is not None:
                if timeout < 0:
                    raise ValueError("timeout should be > 0")

            with pebble.ProcessPool(max_workers=1, max_tasks=1) as pool:
                tasks = pool.schedule(
                    self._run_func,
                    kwargs={
                        "precell_model": precell_model,
                        "postcell_model": postcell_model,
                        "pre_param_values": pre_param_values,
                        "post_param_values": post_param_values,
                        "sim": sim,
                    },
                    timeout=timeout,
                )
                try:
                    responses = tasks.result()
                except FuturesTimeoutError:
                    logger.debug(
                        "SweepProtocol: task took longer than "
                        "timeout, will return empty response "
                        "for this recording"
                    )
                    responses = [
                        {recording.name: None for recording in recordings}
                        for recordings in self.recordings
                    ]
        else:
            responses = self._run_func(
                precell_model=precell_model,
                postcell_model=postcell_model,
                pre_param_values=pre_param_values,
                post_param_values=post_param_values,
                sim=sim,
            )
        return responses

    def instantiate(self, sim=None, pre_icell=None, post_icell=None):
        """Instantiate."""
        icells = [pre_icell, post_icell]

        for i, _ in enumerate(icells):

            for stimulus in self.stimuli[i]:
                stimulus.instantiate(sim=sim, icell=icells[i])

            for recording in self.recordings[i]:
                try:
                    recording.instantiate(sim=sim, icell=icells[i])
                except ephys.locations.EPhysLocInstantiateException:
                    logger.debug(
                        "SweepProtocol: Instantiating recording generated "
                        "location exception, will return empty response for "
                        "this recording"
                    )

    def destroy(self, sim=None):
        """Destroy protocol."""
        for stimulus_list in self.stimuli:
            for stimulus in stimulus_list:
                stimulus.destroy(sim=sim)

        for recording_list in self.recordings:
            for recording in recording_list:
                recording.destroy(sim=sim)

    def __str__(self):
        """String representation."""
        content = "%s:\n" % self.name

        content += "  pre-synaptic stimuli:\n"
        for stimulus in self.stimuli[0]:
            content += "    %s\n" % str(stimulus)

        content += "  post-synaptic stimuli:\n"
        for stimulus in self.stimuli[1]:
            content += "    %s\n" % str(stimulus)

        content += "  pre-synaptic recordings:\n"
        for recording in self.recordings[0]:
            content += "    %s\n" % str(recording)

        content += "  post-synaptic recordings:\n"
        for recording in self.recordings[1]:
            content += "    %s\n" % str(recording)

        return content
