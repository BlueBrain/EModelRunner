"""Protocol reading functions."""

import logging
from bluepyopt import ephys

from emodelrunner.protocols import sscx_protocols
from emodelrunner.locations import SOMA_LOC
from emodelrunner.synapses.stimuli import (
    NrnNetStimStimulusCustom,
    NrnVecStimStimulusCustom,
)


logger = logging.getLogger(__name__)


def read_ramp_threshold_protocol(
    protocol_name, protocol_module, protocol_definition, recordings
):
    """Read ramp threshold protocol from definition.

    Args:
        protocol_name (str): name of the protocol
        protocol_module (module): module that contains the protocol
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
        location=SOMA_LOC,
        total_duration=ramp_definition["totduration"],
    )

    holding_stimulus = ephys.stimuli.NrnSquarePulse(
        step_delay=0.0,
        step_duration=ramp_definition["totduration"],
        location=SOMA_LOC,
        total_duration=ramp_definition["totduration"],
    )

    return protocol_module.RampThresholdProtocol(
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
        location=SOMA_LOC,
        total_duration=ramp_definition["totduration"],
    )

    if "holding" in protocol_definition["stimuli"]:
        holding_definition = protocol_definition["stimuli"]["holding"]
        holding_stimulus = ephys.stimuli.NrnSquarePulse(
            step_amplitude=holding_definition["amp"],
            step_delay=holding_definition["delay"],
            step_duration=holding_definition["duration"],
            location=SOMA_LOC,
            total_duration=holding_definition["totduration"],
        )
    else:
        holding_stimulus = None

    return sscx_protocols.RampProtocol(
        name=protocol_name,
        ramp_stimulus=ramp_stimulus,
        holding_stimulus=holding_stimulus,
        recordings=recordings,
    )


def read_ramp_protocol_from_thalamus_definition(
    protocol_name, protocol_definition, recordings
):
    """Read sscx_protocols.RampProtocol from the thalamus definitions.

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
        ramp_amplitude_start=ramp_definition["ramp_amp_start"],
        ramp_amplitude_end=ramp_definition["ramp_amp_end"],
        ramp_delay=ramp_definition["ramp_delay"],
        ramp_duration=ramp_definition["ramp_duration"],
        location=SOMA_LOC,
        total_duration=ramp_definition["totduration"],
    )

    if "holding" in protocol_definition["stimuli"]:
        holding_definition = protocol_definition["stimuli"]["holding"]
        holding_stimulus = ephys.stimuli.NrnSquarePulse(
            step_amplitude=holding_definition["amp"],
            step_delay=holding_definition["delay"],
            step_duration=holding_definition["duration"],
            location=SOMA_LOC,
            total_duration=holding_definition["totduration"],
        )
    else:
        holding_stimulus = None

    return sscx_protocols.RampProtocol(
        name=protocol_name,
        ramp_stimulus=ramp_stimulus,
        holding_stimulus=holding_stimulus,
        recordings=recordings,
    )


def read_step_protocol(
    protocol_name, protocol_module, protocol_definition, recordings, stochkv_det=None
):
    """Read step protocol from definition.

    Args:
        protocol_name (str): name of the protocol
        protocol_module (module): module that contains the protocol
        protocol_definition (dict): contains the protocol configuration data
        recordings (bluepyopt.ephys.recordings.CompRecording):
            recordings to use with this protocol
        protocol_cls (module): module that contains the protocol
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
            location=SOMA_LOC,
            total_duration=step_definition["totduration"],
        )
        step_stimuli.append(step_stim)

    if "holding" in protocol_definition["stimuli"]:
        holding_definition = protocol_definition["stimuli"]["holding"]
        holding_stimulus = ephys.stimuli.NrnSquarePulse(
            step_amplitude=holding_definition["amp"],
            step_delay=holding_definition["delay"],
            step_duration=holding_definition["duration"],
            location=SOMA_LOC,
            total_duration=holding_definition["totduration"],
        )
    else:
        holding_stimulus = None

    if stochkv_det is None:
        stochkv_det = (
            step_definition["stochkv_det"] if "stochkv_det" in step_definition else None
        )

    return protocol_module.StepProtocol(
        name=protocol_name,
        step_stimuli=step_stimuli,
        holding_stimulus=holding_stimulus,
        recordings=recordings,
        stochkv_det=stochkv_det,
    )


def read_step_threshold_protocol(
    protocol_name, protocol_module, protocol_definition, recordings, stochkv_det=None
):
    """Read step threshold protocol from definition.

    Args:
        protocol_name (str): name of the protocol
        protocol_module (module): module that contains the protocol
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
            location=SOMA_LOC,
            total_duration=step_definition["totduration"],
        )
        step_stimuli.append(step_stim)

    holding_stimulus = ephys.stimuli.NrnSquarePulse(
        step_delay=0.0,
        step_duration=step_definition["totduration"],
        location=SOMA_LOC,
        total_duration=step_definition["totduration"],
    )

    if stochkv_det is None:
        stochkv_det = (
            step_definition["stochkv_det"] if "stochkv_det" in step_definition else None
        )

    return protocol_module.StepThresholdProtocol(
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

    return sscx_protocols.SweepProtocolCustom(protocol_name, [stim], recordings)


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

    return sscx_protocols.SweepProtocolCustom(protocol_name, [stim], recordings)
