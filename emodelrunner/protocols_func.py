"""Protocol-related functions."""

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

import json
import logging

from bluepyopt import ephys

from emodelrunner.protocols import (
    RampProtocol,
    RampThresholdProtocol,
    StepProtocol,
    StepThresholdProtocol,
    RatSSCxThresholdDetectionProtocol,
    RatSSCxRinHoldcurrentProtocol,
    RatSSCxMainProtocol,
    SweepProtocolCustom,
)
from emodelrunner.recordings import RecordingCustom
from emodelrunner.features import define_efeatures
from emodelrunner.synapses.stimuli import (
    NrnNetStimStimulusCustom,
    NrnVecStimStimulusCustom,
)

logger = logging.getLogger(__name__)

soma_loc = ephys.locations.NrnSeclistCompLocation(
    name="soma", seclist_name="somatic", sec_index=0, comp_x=0.5
)
seclist_to_sec = {
    "somatic": "soma",
    "apical": "apic",
    "axonal": "axon",
    "myelinated": "myelin",
}


def read_ramp_threshold_protocol(protocol_name, protocol_definition, recordings):
    """Read ramp threshold protocol from definition.

    Args:
        protocol_name (str): name of the protocol
        protocol_definition (dict): contains the protocol configuration data
        recordings (bluepyopt.ephys.recordings.CompRecording):
            recordings to use with this protocol

    Returns:
        RampThresholdProtocol: Ramp Protocol depending on cell's threshold current
    """
    ramp_definition = protocol_definition["stimuli"]["ramp"]
    ramp_stimulus = ephys.stimuli.NrnRampPulse(
        ramp_delay=ramp_definition["ramp_delay"],
        ramp_duration=ramp_definition["ramp_duration"],
        location=soma_loc,
        total_duration=ramp_definition["totduration"],
    )

    holding_stimulus = ephys.stimuli.NrnSquarePulse(
        step_delay=0.0,
        step_duration=ramp_definition["totduration"],
        location=soma_loc,
        total_duration=ramp_definition["totduration"],
    )

    return RampThresholdProtocol(
        name=protocol_name,
        ramp_stimulus=ramp_stimulus,
        holding_stimulus=holding_stimulus,
        thresh_perc_start=ramp_definition["thresh_perc_start"],
        thresh_perc_end=ramp_definition["thresh_perc_end"],
        recordings=recordings,
    )


def read_ramp_protocol(protocol_name, protocol_definition, recordings):
    """Read ramp protocol from definition.

    Args:
        protocol_name (str): name of the protocol
        protocol_definition (dict): contains the protocol configuration data
        recordings (bluepyopt.ephys.recordings.CompRecording):
            recordings to use with this protocol

    Returns:
        RampProtocol: Ramp Protocol
    """
    ramp_definition = protocol_definition["stimuli"]["ramp"]
    ramp_stimulus = ephys.stimuli.NrnRampPulse(
        ramp_amplitude_start=ramp_definition["ramp_amplitude_start"],
        ramp_amplitude_end=ramp_definition["ramp_amplitude_end"],
        ramp_delay=ramp_definition["ramp_delay"],
        ramp_duration=ramp_definition["ramp_duration"],
        location=soma_loc,
        total_duration=ramp_definition["totduration"],
    )

    if "holding" in protocol_definition["stimuli"]:
        holding_definition = protocol_definition["stimuli"]["holding"]
        holding_stimulus = ephys.stimuli.NrnSquarePulse(
            step_amplitude=holding_definition["amp"],
            step_delay=holding_definition["delay"],
            step_duration=holding_definition["duration"],
            location=soma_loc,
            total_duration=holding_definition["totduration"],
        )
    else:
        holding_stimulus = None

    return RampProtocol(
        name=protocol_name,
        ramp_stimulus=ramp_stimulus,
        holding_stimulus=holding_stimulus,
        recordings=recordings,
    )


def read_step_protocol(
    protocol_name, protocol_definition, recordings, stochkv_det=None
):
    """Read step protocol from definition.

    Args:
        protocol_name (str): name of the protocol
        protocol_definition (dict): contains the protocol configuration data
        recordings (bluepyopt.ephys.recordings.CompRecording):
            recordings to use with this protocol
        stochkv_det (bool): set if stochastic or deterministic

    Returns:
        StepProtocol: Step Protocol
    """
    # pylint: disable=undefined-loop-variable
    step_definitions = protocol_definition["stimuli"]["step"]
    if isinstance(step_definitions, dict):
        step_definitions = [step_definitions]

    step_stimuli = []
    for step_definition in step_definitions:
        step_stim = ephys.stimuli.NrnSquarePulse(
            step_amplitude=step_definition["amp"],
            step_delay=step_definition["delay"],
            step_duration=step_definition["duration"],
            location=soma_loc,
            total_duration=step_definition["totduration"],
        )
        step_stimuli.append(step_stim)

    if "holding" in protocol_definition["stimuli"]:
        holding_definition = protocol_definition["stimuli"]["holding"]
        holding_stimulus = ephys.stimuli.NrnSquarePulse(
            step_amplitude=holding_definition["amp"],
            step_delay=holding_definition["delay"],
            step_duration=holding_definition["duration"],
            location=soma_loc,
            total_duration=holding_definition["totduration"],
        )
    else:
        holding_stimulus = None

    if stochkv_det is None:
        stochkv_det = (
            step_definition["stochkv_det"] if "stochkv_det" in step_definition else None
        )

    return StepProtocol(
        name=protocol_name,
        step_stimuli=step_stimuli,
        holding_stimulus=holding_stimulus,
        recordings=recordings,
        stochkv_det=stochkv_det,
    )


def read_step_threshold_protocol(
    protocol_name, protocol_definition, recordings, stochkv_det=None
):
    """Read step threshold protocol from definition.

    Args:
        protocol_name (str): name of the protocol
        protocol_definition (dict): contains the protocol configuration data
        recordings (bluepyopt.ephys.recordings.CompRecording): recordings to use with this protocol
        stochkv_det (bool): set if stochastic or deterministic

    Returns:
        StepThresholdProtocol: Step Protocol depending on cell's threshold currentd
    """
    # pylint: disable=undefined-loop-variable
    step_definitions = protocol_definition["stimuli"]["step"]
    if isinstance(step_definitions, dict):
        step_definitions = [step_definitions]

    step_stimuli = []
    for step_definition in step_definitions:
        step_stim = ephys.stimuli.NrnSquarePulse(
            step_delay=step_definition["delay"],
            step_duration=step_definition["duration"],
            location=soma_loc,
            total_duration=step_definition["totduration"],
        )
        step_stimuli.append(step_stim)

    holding_stimulus = ephys.stimuli.NrnSquarePulse(
        step_delay=0.0,
        step_duration=step_definition["totduration"],
        location=soma_loc,
        total_duration=step_definition["totduration"],
    )

    if stochkv_det is None:
        stochkv_det = (
            step_definition["stochkv_det"] if "stochkv_det" in step_definition else None
        )

    return StepThresholdProtocol(
        name=protocol_name,
        step_stimuli=step_stimuli,
        holding_stimulus=holding_stimulus,
        thresh_perc=step_definition["thresh_perc"],
        recordings=recordings,
        stochkv_det=stochkv_det,
    )


def read_vecstim_protocol(protocol_name, protocol_definition, recordings, syn_locs):
    """Read Vecstim protocol from definitions.

    Args:
        protocol_name (str): name of the protocol
        protocol_definition (dict): dict containing the protocol data
        recordings (bluepyopt.ephys.recordings.CompRecording):
            recordings to use with this protocol
        syn_locs (list of ephys.locations.NrnPointProcessLocation):
            locations of the synapses

    Returns:
        emodelrunner.protocols.SweepProtocolCustom:
            a protocol containing Vecstim stimulus activating synapses
    """
    stim_definition = protocol_definition["stimuli"]
    if stim_definition["vecstim_random"] not in [
        "python",
        "neuron",
    ]:
        logger.warning(
            "vecstim random not set to 'python' nor to 'neuron' in config file."
            "vecstim random will be re-set to 'python'."
        )
        stim_definition["vecstim_random"] = "python"

    stim = NrnVecStimStimulusCustom(
        syn_locs,
        stim_definition["syn_start"],
        stim_definition["syn_stop"],
        stim_definition["syn_stim_seed"],
        stim_definition["vecstim_random"],
    )

    return SweepProtocolCustom(protocol_name, [stim], recordings)


def read_netstim_protocol(protocol_name, protocol_definition, recordings, syn_locs):
    """Read Netstim protocol from definitions.

    Args:
        protocol_name (str): name of the protocol
        protocol_definition (dict): dict containing the protocol data
        recordings (bluepyopt.ephys.recordings.CompRecording):
            recordings to use with this protocol
        syn_locs (list of ephys.locations.NrnPointProcessLocation):
            locations of the synapses

    Returns:
        emodelrunner.protocols.SweepProtocolCustom:
            a protocol containing Netstim stimulus activating synapses
    """
    stim_definition = protocol_definition["stimuli"]

    stim = NrnNetStimStimulusCustom(
        syn_locs,
        stim_definition["syn_stop"],
        stim_definition["syn_nmb_of_spikes"],
        stim_definition["syn_interval"],
        stim_definition["syn_start"],
        stim_definition["syn_noise"],
    )

    return SweepProtocolCustom(protocol_name, [stim], recordings)


def get_extra_recording_location(recording_definition, apical_point_isec=-1):
    """Get the location for the extra recording.

    Args:
        recording_definition (dict): contains the extra recording configuration data
        apical_point_isec (int): apical point section index.
            Should be given if the recording definition "type" is "somadistanceapic"

    Raises:
        Exception: if the recording definition "type" is "somadistanceapic" and
            apical_point_isec is -1.
        Exception: if the 'type' in the recording definition is neither
            "somadistance", nor "somadistanceapic", nor "nrnseclistcomp"

    Returns:
        location of the extra recording
    """
    if recording_definition["type"] == "somadistance":
        location = ephys.locations.NrnSomaDistanceCompLocation(
            name=recording_definition["name"],
            soma_distance=recording_definition["somadistance"],
            seclist_name=recording_definition["seclist_name"],
        )

    elif recording_definition["type"] == "somadistanceapic":
        if apical_point_isec == -1:
            raise Exception(
                "Cannot record at a given distance from apical point"
                f"if apical_point_isec is {apical_point_isec}."
            )
        location = ephys.locations.NrnSecSomaDistanceCompLocation(
            name=recording_definition["name"],
            soma_distance=recording_definition["somadistance"],
            sec_name=seclist_to_sec[recording_definition["seclist_name"]],
            sec_index=apical_point_isec,
        )

    elif recording_definition["type"] == "nrnseclistcomp":
        location = ephys.locations.NrnSeclistCompLocation(
            name=recording_definition["name"],
            comp_x=recording_definition["comp_x"],
            sec_index=recording_definition["sec_index"],
            seclist_name=recording_definition["seclist_name"],
        )

    else:
        raise Exception(f"Recording type {recording_definition['type']} not supported")

    return location


def get_recordings(protocol_name, protocol_definition, prefix, apical_point_isec=-1):
    """Get recordings from protocol definition.

    Args:
        protocol_name (str): name of the protocol
        protocol_definition (dict): dict containing the protocol data
        prefix (str): prefix used in naming responses, features, recordings, etc.
        apical_point_isec (int): apical point section index
            Should be given if there is "somadistanceapic" in "type"
            of at least one of the extra recording definition

    Returns:
        list of RecordingCustom
    """
    recordings = []
    recordings.append(
        RecordingCustom(
            name=f"{prefix}.{protocol_name}.soma.v",
            location=soma_loc,
            variable="v",
        )
    )

    if "extra_recordings" in protocol_definition:
        for recording_definition in protocol_definition["extra_recordings"]:

            location = get_extra_recording_location(
                recording_definition, apical_point_isec
            )

            var = recording_definition["var"]
            recording = RecordingCustom(
                name=f"{prefix}.{protocol_name}.{location.name}.{var}",
                location=location,
                variable=var,
            )
            recordings.append(recording)

    return recordings


def add_protocol(
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
            protocol_name, protocol_definition, recordings, stochkv_det
        )
    elif (
        "type" in protocol_definition
        and protocol_definition["type"] == "StepThresholdProtocol"
    ):
        protocols_dict[protocol_name] = read_step_threshold_protocol(
            protocol_name, protocol_definition, recordings, stochkv_det
        )
    elif (
        "type" in protocol_definition
        and protocol_definition["type"] == "RampThresholdProtocol"
    ):
        protocols_dict[protocol_name] = read_ramp_threshold_protocol(
            protocol_name, protocol_definition, recordings
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
        protocols_dict["ThresholdDetection"] = RatSSCxThresholdDetectionProtocol(
            "IDRest",
            step_protocol_template=read_step_protocol(
                "Threshold", protocol_definition["step_template"], recordings
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
                    location=soma_loc,
                    total_duration=stimulus_definition["totduration"],
                )
            )

        protocols_dict[protocol_name] = ephys.protocols.SweepProtocol(
            name=protocol_name, stimuli=stimuli, recordings=recordings
        )


def check_for_forbidden_protocol(protocols_dict):
    """Check for unsupported protocol.

    Args:
        protocols_dict (dict): contains all protocols to be run

    Raises:
        Exception: If a protocol that should only be used with MainProtocol is present
            in protocols_dict
    """
    # Those protocols cannot be used if they are not in MainProtocol
    forbidden_prots = [
        "RatSSCxRinHoldcurrentProtocol",
        "RatSSCxThresholdDetectionProtocol",
        "StepThresholdProtocol",
        "RampThresholdProtocol",
    ]
    # check the class name of each protocol
    for prot in protocols_dict.values():
        if type(prot).__name__ in forbidden_prots:
            prot_name = type(prot).__name__
            raise Exception(
                "No MainProtocol found, but {prot} was found."
                f"To use {prot_name}, please set MainProtocol."
            )


def define_protocols(
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
            add_protocol(
                protocols_dict,
                protocol_name,
                protocol_definition,
                recordings,
                stochkv_det,
                prefix,
                syn_locs,
            )

    if "Main" in protocol_definitions.keys():
        protocols_dict["RinHoldcurrent"] = RatSSCxRinHoldcurrentProtocol(
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

        protocols_dict["Main"] = RatSSCxMainProtocol(
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


def create_protocols(
    apical_point_isec,
    prot_path,
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
        features_path (str): path to the features file
        mtype (str): morphology name to be used as prefix in output filenames
        syn_locs (list): list of synapse locations
        stochkv_det (bool): set if stochastic or deterministic

    Returns:
        ephys.protocols.SequenceProtocol: sequence protocol containing all the protocols
    """
    # pylint: disable=unbalanced-tuple-unpacking, too-many-locals
    protocols_dict = define_protocols(
        prot_path,
        stochkv_det,
        mtype,
        apical_point_isec,
        syn_locs,
    )

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
