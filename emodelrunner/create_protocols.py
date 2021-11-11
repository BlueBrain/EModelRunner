"""Protocol creation functions & custom protocol classes."""

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

from emodelrunner.create_recordings import get_pairsim_recordings
from emodelrunner.create_stimuli import load_pulses

from emodelrunner.synplas_protocols import SweepProtocolCustom
from emodelrunner.synplas_protocols import SweepProtocolPairSim
from emodelrunner.protocols_func import create_protocols

from emodelrunner.synapses.recordings import SynapseRecordingCustom
from emodelrunner.stimuli import MultipleSteps
from emodelrunner.synapses.create_locations import get_syn_locs
from emodelrunner.synapses.stimuli import (
    NrnVecStimStimulusCustom,
    NetConSpikeDetector,
)

logger = logging.getLogger(__name__)


class SSCXProtocols:
    """Class representing the protocols applied in SSCX.

    Attributes:
        protocols (bluepyopt.ephys.protocols.SequenceProtocol): the protocols to apply to the cell
    """

    def __init__(
        self,
        add_synapses,
        prot_args,
        cell=None,
    ):
        """Define Protocols.

        Args:
            add_synapses (bool): whether to add synapses to the cell
            prot_args (dict): config data relative to protocols
                See load.get_prot_args for details
            cell (CellModelCustom): cell model
        """
        self.protocols = None

        syn_locs = None
        if add_synapses:
            if cell is not None:
                # locations
                syn_locs = get_syn_locs(cell)
            else:
                raise Exception("The cell is missing in the define_protocol function.")

        self.protocols = create_protocols(
            prot_args["apical_point_isec"],
            mtype=prot_args["mtype"],
            syn_locs=syn_locs,
            prot_path=prot_args["prot_path"],
            features_path=prot_args["features_path"],
        )

    def get_ephys_protocols(self):
        """Returns the list of ephys protocol objects.

        Returns:
            bluepyopt.ephys.protocols.SequenceProtocol: the protocols to apply to the cell
        """
        return self.protocols

    def get_stim_currents(self, responses):
        """Generates the currents injected by protocols.

        Args:
            responses (dict): the responses to the protocols run

        Returns:
            dict: the currents of the protocols.

            If the MainProtocol was used, only the RMP protocol,
            'pre-protocols' and 'other protocols' currents are returned
        """
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
    cell,
    pre_spike_train,
    protocol_name,
    cvode_active,
    synrecs,
    tstop,
    fastforward,
    stim_path="protocols/stimuli.json",
):
    """Create stimuli and protocols to run glusynapse cell.

    Args:
        cell (CellModelCustom): post-synaptic cell model
        pre_spike_train (list): times at which the synapses fire (ms)
        protocol_name (str): protocol name to be passed on to Recording and Protocol classes
        cvode_active (bool): whether to activate the adaptative time step
        synrecs (list of str): the extra synapse variables to record
        tstop (float): total duration of the simulation (ms)
        fastforward (float): time at which to enable synapse fast-forwarding (ms)
        stim_path (str): path to the pulse stimuli file

    Returns:
        synplas_protocols.SweepProtocolCustom: synapse plasticity protocols
    """
    # pylint: disable=too-many-locals
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
    stims = load_pulses(soma_loc, stim_path)

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
    stim_path="protocols/stimuli.json",
):
    """Create stimuli and protocols to run glusynapse cell.

    Args:
        postcell (CellModelCustom): post-synaptic cell model
        presyn_prot_name (str): presynaptic protocol name
            to be passed on to Recording and Protocol classes
        postsyn_prot_name (str): postsynaptic protocol name
            to be passed on to Recording and Protocol classes
        cvode_active (bool): whether to activate the adaptative time step
        synrecs (list of str): the extra synapse variables to record
        tstop (float): total duration of the simulation (ms)
        fastforward (float): time at which to enable synapse fast-forwarding (ms)
        presyn_stim_args (dict): presynaptic stimulus configuration data
            See load.get_presyn_stim_args for details
        stim_path (str): path to the pulse stimuli file

    Returns:
        synplas_protocols.SweepProtocolPairSim: pair simulation synapse plasticity protocols
    """
    # pylint: disable=too-many-arguments, too-many-locals
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
    postsyn_stims = load_pulses(soma_loc, stim_path)

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
