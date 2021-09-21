"""Protocol creation functions & custom protocol classes."""
import logging

from bluepyopt import ephys

from emodelrunner.create_recordings import get_pairsim_recordings
from emodelrunner.create_stimuli import load_pulses

from emodelrunner.synplas_protocols import SweepProtocolCustom
from emodelrunner.synplas_protocols import SweepProtocolPairSim
from emodelrunner.protocols_func import (
    create_protocols as create_recipe_protocols,
)

from emodelrunner.recordings import SynapseRecordingCustom
from emodelrunner.stimuli import MultipleSteps
from emodelrunner.synapses.create_locations import get_syn_locs
from emodelrunner.synapses.stimuli import (
    NrnVecStimStimulusCustom,
    NetConSpikeDetector,
)

logger = logging.getLogger(__name__)


class SSCXProtocols:
    """Class representing the protocols applied in SSCX."""

    def __init__(
        self,
        add_synapses,
        prot_args,
        cell=None,
    ):
        """Define Protocols."""
        self.protocols = None

        syn_locs = None
        if add_synapses:
            if cell is not None:
                # locations
                syn_locs = get_syn_locs(cell)
            else:
                raise Exception("The cell is missing in the define_protocol function.")

        self.protocols = create_recipe_protocols(
            prot_args["apical_point_isec"],
            mtype=prot_args["mtype"],
            syn_locs=syn_locs,
            prot_path=prot_args["prot_path"],
            features_path=prot_args["features_path"],
        )

    def get_ephys_protocols(self):
        """Returns the list of ephys protocol objects."""
        return self.protocols

    def get_stim_currents(self, responses):
        """Generates the currents injected by protocols."""
        currents = {}

        # find threshold and holding currents
        thres_i = None
        hold_i = None
        for key, resp in responses.items():
            if "threshold_current" in key:
                thres_i = resp
            elif "holding_current" in key:
                hold_i = resp

        currents = {}
        for protocol in self.protocols.protocols:
            currents.update(
                protocol.generate_current(
                    threshold_current=thres_i, holding_current=hold_i
                )
            )

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
    protocol_name = (
        f"presynaptic protocol: {presyn_prot_name},"
        + f"postsynaptic protocol: {postsyn_prot_name}"
    )
    return SweepProtocolPairSim(
        protocol_name,
        (presyn_stims, postsyn_stims),
        recs,
        cvode_active,
        fastforward,
    )
