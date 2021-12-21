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
import json

from bluepyopt import ephys

from emodelrunner.protocols import sscx_protocols
from emodelrunner.create_recordings import get_pairsim_recordings
from emodelrunner.create_stimuli import load_pulses
from emodelrunner.configuration import PackageType
from emodelrunner.protocols import synplas_protocols

from emodelrunner.synapses.recordings import SynapseRecordingCustom
from emodelrunner.stimuli import MultipleSteps
from emodelrunner.features import define_efeatures
from emodelrunner.locations import SOMA_LOC
from emodelrunner.protocols.protocols_func import (
    check_for_forbidden_protocol,
    get_recordings,
)
from emodelrunner.protocols.reader import (
    read_step_protocol,
    read_step_threshold_protocol,
    read_ramp_protocol,
    read_ramp_threshold_protocol,
    read_vecstim_protocol,
    read_netstim_protocol,
)
from emodelrunner.synapses.create_locations import get_syn_locs
from emodelrunner.synapses.stimuli import (
    NrnVecStimStimulusCustom,
    NetConSpikeDetector,
)

logger = logging.getLogger(__name__)


class ProtocolBuilder:
    """Class representing the protocols applied in SSCX.

    Attributes:
        protocols (bluepyopt.ephys.protocols.SequenceProtocol): the protocols to apply to the cell
    """

    def __init__(self, protocols):
        """Constructor to be called by the classmethod overloads."""
        self.protocols = protocols

    @classmethod
    def using_sscx_protocols(cls, add_synapses, prot_args, cell=None):
        """Creates the object with the sscx protocols.

        Args:
            add_synapses (bool): whether to add synapses to the cell
            prot_args (dict): config data relative to protocols
                See load.get_prot_args for details
            cell (CellModelCustom): cell model
        """
        syn_locs = None
        if add_synapses:
            if cell is not None:
                # locations
                syn_locs = get_syn_locs(cell)
            else:
                raise Exception("The cell is missing in the define_protocol function.")

        protocols = create_protocols_object(
            apical_point_isec=prot_args["apical_point_isec"],
            prot_path=prot_args["prot_path"],
            package_type=PackageType.sscx,
            features_path=prot_args["features_path"],
            mtype=prot_args["mtype"],
            syn_locs=syn_locs,
        )
        return cls(protocols)

    @classmethod
    def using_thalamus_protocols(cls, add_synapses, prot_args, cell=None):
        """Creates the object with the thalamus protocols.

        Args:
            add_synapses (bool): whether to add synapses to the cell
            prot_args (dict): config data relative to protocols
                See load.get_prot_args for details
            cell (CellModelCustom): cell model
        """
        syn_locs = None
        if add_synapses:
            if cell is not None:
                # locations
                syn_locs = get_syn_locs(cell)
            else:
                raise Exception("The cell is missing in the define_protocol function.")

        protocols = create_protocols_object(
            apical_point_isec=prot_args["apical_point_isec"],
            prot_path=prot_args["prot_path"],
            package_type=PackageType.thalamus,
            features_path=prot_args["features_path"],
            mtype=prot_args["mtype"],
            syn_locs=syn_locs,
        )
        return cls(protocols)

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


def create_protocols_object(
    apical_point_isec,
    prot_path,
    package_type,
    features_path="",
    mtype="",
    syn_locs=None,
    stochkv_det=None,
):
    """Return a dict containing protocols.

    Args:
        apical_point_isec (int): section index of the apical point
            Set to -1 no apical point is used in any extra recordings
        prot_path (str): path to the protocols file
        package_type (Enum): enum denoting the package type
        features_path (str): path to the features file
        mtype (str): morphology name to be used as prefix in output filenames
        syn_locs (list): list of synapse locations
        stochkv_det (bool): set if stochastic or deterministic

    Returns:
        ephys.protocols.SequenceProtocol: sequence protocol containing all the protocols
    """
    # pylint: disable=unbalanced-tuple-unpacking, too-many-locals
    if package_type == PackageType.sscx:
        protocols_dict = define_sscx_protocols(
            prot_path,
            stochkv_det,
            mtype,
            apical_point_isec,
            syn_locs,
        )
    elif package_type == PackageType.thalamus:
        protocols_dict = define_thalamus_protocols(
            prot_path,
            stochkv_det,
            mtype,
            apical_point_isec,
            syn_locs,
        )
    else:
        raise ValueError(f"unsupported package type: {package_type}")

    if "Main" in protocols_dict:
        efeatures = define_efeatures(
            protocols_dict["Main"],
            features_path,
            mtype,
        )

        set_main_protocol_efeatures(protocols_dict, efeatures, mtype)

        protocols = [protocols_dict["Main"]]
    else:
        protocols = list(protocols_dict.values())

    return ephys.protocols.SequenceProtocol(
        "all protocols",
        protocols=protocols,
    )


def define_sscx_protocols(
    protocols_filepath,
    stochkv_det=None,
    prefix="",
    apical_point_isec=-1,
    syn_locs=None,
):
    """Define protocols.

    Args:
        protocols_filename (str): path to the protocols file
        stochkv_det (bool): set if stochastic or deterministic
        prefix (str): prefix used in naming responses, features, recordings, etc.
        apical_point_isec (int): apical point section index
            Should be given if there is "somadistanceapic" in "type"
            of at least one of the extra recordings
        syn_locs (list of ephys.locations.NrnPointProcessLocation):
            locations of the synapses (if any, else None)

    Returns:
        dict containing the protocols
    """
    with open(protocols_filepath, "r", encoding="utf-8") as protocol_file:
        protocol_definitions = json.load(protocol_file)

    if "__comment" in protocol_definitions:
        del protocol_definitions["__comment"]

    protocols_dict = {}

    for protocol_name, protocol_definition in protocol_definitions.items():
        if protocol_name not in ["Main", "RinHoldcurrent"]:

            recordings = get_recordings(
                protocol_name, protocol_definition, prefix, apical_point_isec
            )

            # add protocol to protocol dict
            add_protocol_to_dict(
                protocols_dict,
                protocol_name,
                protocol_definition,
                recordings,
                stochkv_det,
                prefix,
                syn_locs,
            )

    if "Main" in protocol_definitions.keys():
        protocols_dict["RinHoldcurrent"] = sscx_protocols.RatSSCxRinHoldcurrentProtocol(
            "RinHoldCurrent",
            rin_protocol_template=protocols_dict["Rin"],
            holdi_precision=protocol_definitions["RinHoldcurrent"]["holdi_precision"],
            holdi_max_depth=protocol_definitions["RinHoldcurrent"]["holdi_max_depth"],
            prefix=prefix,
        )

        other_protocols = []

        for protocol_name in protocol_definitions["Main"]["other_protocols"]:
            if protocol_name in protocols_dict:
                other_protocols.append(protocols_dict[protocol_name])

        pre_protocols = []

        if "pre_protocols" in protocol_definitions["Main"]:
            for protocol_name in protocol_definitions["Main"]["pre_protocols"]:
                pre_protocols.append(protocols_dict[protocol_name])

        protocols_dict["Main"] = sscx_protocols.RatSSCxMainProtocol(
            "Main",
            rmp_protocol=protocols_dict["RMP"],
            rinhold_protocol=protocols_dict["RinHoldcurrent"],
            thdetect_protocol=protocols_dict["ThresholdDetection"],
            other_protocols=other_protocols,
            pre_protocols=pre_protocols,
        )
    else:
        check_for_forbidden_protocol(protocols_dict)

    return protocols_dict


def define_thalamus_protocols(
    protocols_filepath,
    stochkv_det=None,
    prefix="",
    apical_point_isec=-1,
    syn_locs=None,
):
    """Return dict containing the protocols used in thalamus packages."""
    raise NotImplementedError("This function is not implemented yet.")


def set_main_protocol_efeatures(protocols_dict, efeatures, prefix):
    """Set the efeatures of the main protocol.

    Args:
        protocols_dict (dict): contains all protocols to be run
            If this function is called, should contain the MainProtocol
            and the associated protocols (RinHoldCurrent, ThresholdDetection)
        efeatures (dict): contains the efeatures
        prefix (str): prefix used in naming responses, features, recordings, etc.
    """
    protocols_dict["Main"].rmp_efeature = efeatures[f"{prefix}.RMP.soma.v.voltage_base"]

    protocols_dict["Main"].rin_efeature = efeatures[
        f"{prefix}.Rin.soma.v.ohmic_input_resistance_vb_ssse"
    ]

    protocols_dict["Main"].rin_efeature.stimulus_current = protocols_dict[
        "Main"
    ].rinhold_protocol.rin_protocol_template.step_amplitude

    protocols_dict["RinHoldcurrent"].voltagebase_efeature = efeatures[
        f"{prefix}.Rin.soma.v.voltage_base"
    ]
    protocols_dict["ThresholdDetection"].holding_voltage = efeatures[
        f"{prefix}.Rin.soma.v.voltage_base"
    ].exp_mean


def add_protocol_to_dict(
    protocols_dict,
    protocol_name,
    protocol_definition,
    recordings,
    stochkv_det,
    prefix,
    syn_locs=None,
):
    """Add protocol from protocol definition to protocols dict.

    Args:
        protocols_dict (dict): the dict to which to append the protocol
        protocol_name (str): name of the protocol
        protocol_definition (dict): dict containing the protocol data
        recordings (bluepyopt.ephys.recordings.CompRecording): recordings to use with this protocol
        stochkv_det (bool): set if stochastic or deterministic
        prefix (str): prefix used in naming responses, features, recordings, etc.
        syn_locs (list of ephys.locations.NrnPointProcessLocation): locations of the synapses
            (if any, else None)
    """
    if "type" in protocol_definition and protocol_definition["type"] == "StepProtocol":
        protocols_dict[protocol_name] = read_step_protocol(
            protocol_name, sscx_protocols, protocol_definition, recordings, stochkv_det
        )
    elif (
        "type" in protocol_definition
        and protocol_definition["type"] == "StepThresholdProtocol"
    ):
        protocols_dict[protocol_name] = read_step_threshold_protocol(
            protocol_name, sscx_protocols, protocol_definition, recordings, stochkv_det
        )
    elif (
        "type" in protocol_definition
        and protocol_definition["type"] == "RampThresholdProtocol"
    ):
        protocols_dict[protocol_name] = read_ramp_threshold_protocol(
            protocol_name, sscx_protocols, protocol_definition, recordings
        )
    elif (
        "type" in protocol_definition and protocol_definition["type"] == "RampProtocol"
    ):
        protocols_dict[protocol_name] = read_ramp_protocol(
            protocol_name, protocol_definition, recordings
        )
    elif (
        "type" in protocol_definition
        and protocol_definition["type"] == "RatSSCxThresholdDetectionProtocol"
    ):
        protocols_dict[
            "ThresholdDetection"
        ] = sscx_protocols.RatSSCxThresholdDetectionProtocol(
            "IDRest",
            step_protocol_template=read_step_protocol(
                "Threshold",
                sscx_protocols,
                protocol_definition["step_template"],
                recordings,
            ),
            prefix=prefix,
        )
    elif "type" in protocol_definition and protocol_definition["type"] == "Vecstim":
        protocols_dict[protocol_name] = read_vecstim_protocol(
            protocol_name, protocol_definition, recordings, syn_locs
        )
    elif "type" in protocol_definition and protocol_definition["type"] == "Netstim":
        protocols_dict[protocol_name] = read_netstim_protocol(
            protocol_name, protocol_definition, recordings, syn_locs
        )
    else:
        stimuli = []
        for stimulus_definition in protocol_definition["stimuli"]:
            stimuli.append(
                ephys.stimuli.NrnSquarePulse(
                    step_amplitude=stimulus_definition["amp"],
                    step_delay=stimulus_definition["delay"],
                    step_duration=stimulus_definition["duration"],
                    location=SOMA_LOC,
                    total_duration=stimulus_definition["totduration"],
                )
            )

        protocols_dict[protocol_name] = ephys.protocols.SweepProtocol(
            name=protocol_name, stimuli=stimuli, recordings=recordings
        )


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
    return synplas_protocols.SweepProtocolCustom(
        protocol_name, stims, recs, cvode_active, fastforward
    )


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
    return synplas_protocols.SweepProtocolPairSim(
        protocol_name,
        (presyn_stims, postsyn_stims),
        recs,
        cvode_active,
        fastforward,
    )
