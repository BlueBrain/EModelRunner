"""Protocol creation functions & custom protocol classes."""
import logging

from bluepyopt import ephys

from emodelrunner.create_recordings import get_pairsim_recordings
from emodelrunner.create_stimuli import load_pulses
from emodelrunner.create_stimuli import generate_current
from emodelrunner.create_stimuli import get_step_stimulus
from emodelrunner.load import load_amps
from emodelrunner.protocols import SweepProtocolCustom
from emodelrunner.protocols import SweepProtocolPairSim
from emodelrunner.recordings import RecordingCustom
from emodelrunner.recordings import SynapseRecordingCustom
from emodelrunner.stimuli import MultipleSteps
from emodelrunner.synapses.create_locations import get_syn_locs
from emodelrunner.synapses.create_stimuli import get_syn_stim
from emodelrunner.synapses.stimuli import (
    NrnVecStimStimulusCustom,
    NetConSpikeDetector,
)

logger = logging.getLogger(__name__)


def get_step_numbers(run_all_steps, run_step_number, step_number=3):
    """Return the first and last step +1 to be run."""
    if run_all_steps:
        return 0, step_number
    elif run_step_number in range(1, step_number + 1):
        return run_step_number - 1, run_step_number
    else:
        logger.warning(
            " ".join(
                (
                    "Bad run_step_number parameter.",
                    "Should be between 1 and {}.".format(step_number),
                    "Only first step will be run.",
                )
            )
        )
        return 0, 1


def get_step_protocol(
    amps_path,
    step_args,
    soma_loc,
    cvode_active=False,
    syn_stim=None,
):
    """Create Step Stimuli and return the Protocols for all stimuli."""
    # pylint: disable=too-many-locals
    # get current amplitude data
    amplitudes, hypamp = load_amps(amps_path)

    # get step numbers to run
    from_step, up_to = get_step_numbers(
        step_args["run_all_steps"], step_args["run_step_number"]
    )

    # protocol names
    protocol_names = ["step{}".format(x) for x in range(1, 4)]

    step_protocols = []
    for protocol_name, amplitude in zip(
        protocol_names[from_step:up_to], amplitudes[from_step:up_to]
    ):
        # use RecordingCustom to sample time, voltage every 0.1 ms.
        rec = RecordingCustom(name=protocol_name, location=soma_loc, variable="v")

        stims = get_step_stimulus(step_args, amplitude, hypamp, soma_loc, syn_stim)

        protocol = ephys.protocols.SweepProtocol(
            protocol_name, stims, [rec], cvode_active
        )

        step_protocols.append(protocol)

    return step_protocols


class SSCXProtocols:
    """Class representing the protocols applied in SSCX."""

    def __init__(
        self,
        step_args,
        syn_args,
        step_stim,
        add_synapses,
        amps_path,
        cvode_active,
        cell=None,
    ):
        """Define Protocols."""
        self.step_args = step_args
        self.amplitudes, self.hypamp = load_amps(amps_path)
        self.protocols = None

        # synapses location and stimuli
        if add_synapses and syn_args["syn_stim_mode"] in ["vecstim", "netstim"]:
            if cell is not None:
                # locations
                syn_locs = get_syn_locs(cell)
                # get synpase stimuli
                syn_stim = get_syn_stim(syn_locs, syn_args)
            else:
                raise Exception("The cell is missing in the define_protocol function.")
        else:
            syn_stim = None

        # recording location
        soma_loc = ephys.locations.NrnSeclistCompLocation(
            name="soma", seclist_name="somatic", sec_index=0, comp_x=0.5
        )
        # get step stimuli and make protocol(s)
        if step_stim:
            # get step protocols
            protocols = get_step_protocol(
                amps_path, self.step_args, soma_loc, cvode_active, syn_stim
            )
        elif syn_stim:
            protocol_name = syn_args["syn_stim_mode"]
            # use RecordingCustom to sample time, voltage every 0.1 ms.
            rec = RecordingCustom(name=protocol_name, location=soma_loc, variable="v")

            protocol = ephys.protocols.SweepProtocol(
                protocol_name, [syn_stim], [rec], cvode_active
            )
            protocols = [protocol]
        else:
            raise Exception(
                "No valid protocol was found. step_stimulus is {}".format(step_stim)
                + " and syn_stim_mode ({}) not in ['vecstim', 'netstim'].".format(
                    syn_args["syn_stim_mode"]
                )
            )

        self.protocols = ephys.protocols.SequenceProtocol(
            "twostep", protocols=protocols
        )

    def get_ephys_protocols(self):
        """Returns the list of ephys protocol objects."""
        return self.protocols

    def get_stim_currents(self):
        """Generates the currents injected by protocols."""
        stim_start = self.step_args["step_delay"]
        step_duration = self.step_args["step_duration"]
        stim_end = stim_start + step_duration
        total_duration = self.step_args["total_duration"]
        holding_current = self.hypamp

        currents = []
        for amplitude in self.amplitudes:
            current = generate_current(
                total_duration, holding_current, stim_start, stim_end, amplitude
            )
            currents.append(current)

        return currents


def define_synapse_plasticity_protocols(
    cell, pre_spike_train, protocol_name, cvode_active, synrecs, tstop, fastforward
):
    """Create stimuli and protocols to run glusynapse cell."""
    syn_locs = get_syn_locs(cell)
    syn_stim = NrnVecStimStimulusCustom(
        syn_locs,
        stop=tstop,
        pre_spike_train=pre_spike_train,
    )

    # recording location
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma", seclist_name="somatic", sec_index=0, comp_x=0.5
    )
    # recording
    rec = ephys.recordings.CompRecording(
        name=protocol_name, location=soma_loc, variable="v"
    )
    recs = [rec]

    for syn_loc in syn_locs:
        for synrec in synrecs:
            recs.append(
                SynapseRecordingCustom(name=synrec, location=syn_loc, variable=synrec)
            )

    # pulses
    stims = load_pulses(soma_loc)

    stims.append(syn_stim)

    # create protocol
    return SweepProtocolCustom(protocol_name, stims, recs, cvode_active, fastforward)


def define_pairsim_protocols(
    postcell,
    presyn_prot_name,
    postsyn_prot_name,
    cvode_active,
    synrecs,
    tstop,
    fastforward,
    presyn_stim_args,
):
    """Create stimuli and protocols to run glusynapse cell."""
    # locations
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma", seclist_name="somatic", sec_index=0, comp_x=0.5
    )
    syn_locs = get_syn_locs(postcell)

    # recordings
    # has the structure (precell_recs, postcell_recs)
    recs = get_pairsim_recordings(
        soma_loc, syn_locs, synrecs, presyn_prot_name, postsyn_prot_name
    )

    # stimuli
    postsyn_stims = load_pulses(soma_loc)

    presyn_stims = [
        MultipleSteps(
            soma_loc,
            presyn_stim_args["stim_train"],
            presyn_stim_args["amp"],
            presyn_stim_args["width"],
        )
    ]

    # appened to presyn stim because the precell is needed
    # to activate the postcell synapses
    syn_stim = NetConSpikeDetector(total_duration=tstop, locations=syn_locs)
    presyn_stims.append(syn_stim)

    # create protocol
    protocol_name = "presynaptic protocol: {}, postsynaptic protocol: {}".format(
        presyn_prot_name, postsyn_prot_name
    )
    return SweepProtocolPairSim(
        protocol_name,
        (presyn_stims, postsyn_stims),
        recs,
        cvode_active,
        fastforward,
    )
