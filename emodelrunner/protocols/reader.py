"""Protocol reading functions."""

import logging
import json
from bluepyopt import ephys

from emodelrunner.protocols import sscx_protocols, thalamus_protocols
from emodelrunner.locations import SOMA_LOC
from emodelrunner.synapses.stimuli import (
    NrnNetStimStimulusCustom,
    NrnVecStimStimulusCustom,
)
from emodelrunner.protocols.protocols_func import (
    check_for_forbidden_protocol,
    get_recordings,
)


logger = logging.getLogger(__name__)


class ProtocolParser:
    """Parses the protocol json file."""

    def __init__(self) -> None:
        """Constructor.

        Attributes:
            protocols_dict (dict): protocols parsed into dict.
        """
        self.protocols_dict = {}

    @staticmethod
    def load_protocol_json(protocols_filepath):
        """Loads the protocol json file.

        Args:
            protocols_filepath (str or Path): path to the protocols file.

        Returns:
            dict: dict containing protocols json input.
        """
        with open(protocols_filepath, "r", encoding="utf-8") as protocol_file:
            protocol_definitions = json.load(protocol_file)

        if "__comment" in protocol_definitions:
            del protocol_definitions["__comment"]

        return protocol_definitions

    def _parse_step_and_ramp(
        self,
        protocol_definition,
        protocol_name,
        protocol_module,
        recordings,
        stochkv_det,
    ):
        """Parses the step and ramp protocols into self.protocols_dict."""
        if protocol_definition["type"] == "StepProtocol":
            self.protocols_dict[protocol_name] = read_step_protocol(
                protocol_name,
                protocol_module,
                protocol_definition,
                recordings,
                stochkv_det,
            )
        elif protocol_definition["type"] == "StepThresholdProtocol":
            self.protocols_dict[protocol_name] = read_step_threshold_protocol(
                protocol_name,
                protocol_module,
                protocol_definition,
                recordings,
                stochkv_det,
            )
        elif protocol_definition["type"] == "RampThresholdProtocol":
            self.protocols_dict[protocol_name] = read_ramp_threshold_protocol(
                protocol_name,
                protocol_module,
                protocol_definition,
                recordings,
            )
        elif protocol_definition["type"] == "RampProtocol":
            if protocol_module is sscx_protocols:
                self.protocols_dict[protocol_name] = read_ramp_protocol(
                    protocol_name, protocol_definition, recordings
                )
            elif protocol_module is thalamus_protocols:
                self.protocols_dict[
                    protocol_name
                ] = read_ramp_protocol_from_thalamus_definition(
                    protocol_name, protocol_definition, recordings
                )
            else:
                raise ValueError(f"unsupported protocol module: {protocol_module}")

    def _parse_sscx_threshold_detection(self, protocol_definition, recordings, prefix):
        """Parses the sscx threshold detection protocol into self.protocols_dict."""
        if protocol_definition["type"] == "RatSSCxThresholdDetectionProtocol":
            self.protocols_dict[
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

    def _parse_thalamus_threshold_detection(
        self, protocol_definition, recordings, prefix
    ):
        """Parses the thalamus threshold detection protocol into self.protocols_dict."""
        if protocol_definition["type"] == "RatSSCxThresholdDetectionProtocol":
            self.protocols_dict[
                "ThresholdDetection_dep"
            ] = thalamus_protocols.RatSSCxThresholdDetectionProtocol(
                "ThresholdDetection_dep",
                step_protocol_template=read_step_protocol(
                    "ThresholdDetection_dep",
                    thalamus_protocols,
                    protocol_definition["step_template"],
                    recordings,
                ),
                prefix=prefix,
            )
            self.protocols_dict[
                "ThresholdDetection_hyp"
            ] = thalamus_protocols.RatSSCxThresholdDetectionProtocol(
                "ThresholdDetection_hyp",
                step_protocol_template=read_step_protocol(
                    "ThresholdDetection_hyp",
                    thalamus_protocols,
                    protocol_definition["step_template"],
                    recordings,
                ),
                prefix=prefix,
            )

    def _parse_vecstim_netstim(
        self, protocol_definition, protocol_name, recordings, syn_locs
    ):
        """Parses the vecstim netstim protocols into self.protocols_dict."""
        if protocol_definition["type"] == "Vecstim":
            self.protocols_dict[protocol_name] = read_vecstim_protocol(
                protocol_name, protocol_definition, recordings, syn_locs
            )
        elif protocol_definition["type"] == "Netstim":
            self.protocols_dict[protocol_name] = read_netstim_protocol(
                protocol_name, protocol_definition, recordings, syn_locs
            )

    def _parse_sscx_main(self, protocol_definitions, prefix):
        """Parses the main sscx protocol into self.protocols_dict."""
        self.protocols_dict[
            "RinHoldcurrent"
        ] = sscx_protocols.RatSSCxRinHoldcurrentProtocol(
            "RinHoldCurrent",
            rin_protocol_template=self.protocols_dict["Rin"],
            holdi_precision=protocol_definitions["RinHoldcurrent"]["holdi_precision"],
            holdi_max_depth=protocol_definitions["RinHoldcurrent"]["holdi_max_depth"],
            prefix=prefix,
        )

        other_protocols = []

        for protocol_name in protocol_definitions["Main"]["other_protocols"]:
            if protocol_name in self.protocols_dict:
                other_protocols.append(self.protocols_dict[protocol_name])

        pre_protocols = []

        if "pre_protocols" in protocol_definitions["Main"]:
            for protocol_name in protocol_definitions["Main"]["pre_protocols"]:
                pre_protocols.append(self.protocols_dict[protocol_name])

        self.protocols_dict["Main"] = sscx_protocols.RatSSCxMainProtocol(
            "Main",
            rmp_protocol=self.protocols_dict["RMP"],
            rinhold_protocol=self.protocols_dict["RinHoldcurrent"],
            thdetect_protocol=self.protocols_dict["ThresholdDetection"],
            other_protocols=other_protocols,
            pre_protocols=pre_protocols,
        )

    def _parse_thalamus_main(self, protocol_definitions, prefix):
        """Parses the main thalamus protocol into self.protocols_dict."""
        try:  # Only low-threshold bursting cells have thin protocol
            self.protocols_dict[
                "RinHoldcurrent_dep"
            ] = thalamus_protocols.RatSSCxRinHoldcurrentProtocol(
                "RinHoldCurrent_dep",
                rin_protocol_template=self.protocols_dict["Rin_dep"],
                holdi_estimate_multiplier=protocol_definitions["RinHoldcurrent_dep"][
                    "holdi_estimate_multiplier"
                ],
                holdi_precision=protocol_definitions["RinHoldcurrent_dep"][
                    "holdi_precision"
                ],
                holdi_max_depth=protocol_definitions["RinHoldcurrent_dep"][
                    "holdi_max_depth"
                ],
                prefix=prefix,
            )
            rinhold_protocol_dep = self.protocols_dict["RinHoldcurrent_dep"]
            thdetect_protocol_dep = self.protocols_dict["ThresholdDetection_dep"]
        except KeyError:
            rinhold_protocol_dep = None
            thdetect_protocol_dep = None

        self.protocols_dict[
            "RinHoldcurrent_hyp"
        ] = thalamus_protocols.RatSSCxRinHoldcurrentProtocol(
            "RinHoldCurrent_hyp",
            rin_protocol_template=self.protocols_dict["Rin_hyp"],
            holdi_estimate_multiplier=protocol_definitions["RinHoldcurrent_hyp"][
                "holdi_estimate_multiplier"
            ],
            holdi_precision=protocol_definitions["RinHoldcurrent_hyp"][
                "holdi_precision"
            ],
            holdi_max_depth=protocol_definitions["RinHoldcurrent_hyp"][
                "holdi_max_depth"
            ],
            prefix=prefix,
        )

        other_protocols = []

        for protocol_name in protocol_definitions["Main"]["other_protocols"]:
            other_protocols.append(self.protocols_dict[protocol_name])

        pre_protocols = []
        preprot_score_threshold = 1

        if "pre_protocols" in protocol_definitions["Main"]:
            for protocol_name in protocol_definitions["Main"]["pre_protocols"]:
                pre_protocols.append(self.protocols_dict[protocol_name])
            preprot_score_threshold = protocol_definitions["Main"][
                "preprot_score_threshold"
            ]

        runopt = False
        self.protocols_dict["Main"] = thalamus_protocols.RatSSCxMainProtocol(
            "Main",
            rmp_protocol=self.protocols_dict["RMP"],
            rmp_score_threshold=protocol_definitions["Main"]["rmp_score_threshold"],
            rinhold_protocol_dep=rinhold_protocol_dep,
            rinhold_protocol_hyp=self.protocols_dict["RinHoldcurrent_hyp"],
            rin_score_threshold=protocol_definitions["Main"]["rin_score_threshold"],
            thdetect_protocol_dep=thdetect_protocol_dep,
            thdetect_protocol_hyp=self.protocols_dict["ThresholdDetection_hyp"],
            other_protocols=other_protocols,
            pre_protocols=pre_protocols,
            preprot_score_threshold=preprot_score_threshold,
            use_rmp_rin_thresholds=runopt,
        )

    def parse_sscx_protocols(
        self,
        protocols_filepath,
        stochkv_det=None,
        prefix="",
        apical_point_isec=-1,
        syn_locs=None,
    ):
        """Parses the SSCX protocols from the json file input.

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
        protocol_definitions = self.load_protocol_json(protocols_filepath)

        # fmt: off
        protocols_with_type = [
            "StepProtocol", "StepThresholdProtocol", "RampThresholdProtocol",
            "RampProtocol", "RatSSCxThresholdDetectionProtocol", "Vecstim", "Netstim"]
        # fmt: on

        for protocol_name, protocol_definition in protocol_definitions.items():
            if protocol_name not in ["Main", "RinHoldcurrent"]:
                recordings = get_recordings(
                    protocol_name, protocol_definition, prefix, apical_point_isec
                )

                if "type" in protocol_definition:
                    # add protocol to protocol dict
                    self._parse_step_and_ramp(
                        protocol_definition,
                        protocol_name,
                        sscx_protocols,
                        recordings,
                        stochkv_det,
                    )
                    self._parse_sscx_threshold_detection(
                        protocol_definition, recordings, prefix
                    )
                    self._parse_vecstim_netstim(
                        protocol_definition, protocol_name, recordings, syn_locs
                    )

                elif (
                    "type" not in protocol_definition
                    or protocol_definition["type"] not in protocols_with_type
                ):
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

                    self.protocols_dict[protocol_name] = ephys.protocols.SweepProtocol(
                        name=protocol_name, stimuli=stimuli, recordings=recordings
                    )

        if "Main" in protocol_definitions.keys():
            self._parse_sscx_main(protocol_definitions, prefix)
        else:
            check_for_forbidden_protocol(self.protocols_dict)

        return self.protocols_dict

    def parse_thalamus_protocols(
        self,
        protocols_filepath,
        stochkv_det=None,
        prefix="",
        apical_point_isec=-1,
    ):
        """Parses the Thalamus protocols from the json file input.

        Args:
            protocols_filename (str): path to the protocols file
            stochkv_det (bool): set if stochastic or deterministic
            prefix (str): prefix used in naming responses, features, recordings, etc.
            apical_point_isec (int): apical point section index
                Should be given if there is "somadistanceapic" in "type"
                of at least one of the extra recordings

        Returns:
            dict containing the protocols
        """
        protocol_definitions = self.load_protocol_json(protocols_filepath)

        # fmt: off
        protocols_with_type = [
            "StepProtocol", "StepThresholdProtocol", "RampThresholdProtocol",
            "RampProtocol", "RatSSCxThresholdDetectionProtocol"]
        # fmt: on

        for protocol_name, protocol_definition in protocol_definitions.items():
            if protocol_name not in ["Main", "RinHoldcurrent"]:
                recordings = get_recordings(
                    protocol_name, protocol_definition, prefix, apical_point_isec
                )

                if "type" in protocol_definition:
                    # add protocol to protocol dict
                    self._parse_step_and_ramp(
                        protocol_definition,
                        protocol_name,
                        thalamus_protocols,
                        recordings,
                        stochkv_det,
                    )
                    self._parse_thalamus_threshold_detection(
                        protocol_definition, recordings, prefix
                    )

                elif (
                    "type" not in protocol_definition
                    or protocol_definition["type"] not in protocols_with_type
                ):
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

                    self.protocols_dict[protocol_name] = ephys.protocols.SweepProtocol(
                        name=protocol_name, stimuli=stimuli, recordings=recordings
                    )

        if "Main" in protocol_definitions.keys():
            self._parse_thalamus_main(protocol_definitions, prefix)
        else:
            check_for_forbidden_protocol(self.protocols_dict)

        return self.protocols_dict


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

    if protocol_module is thalamus_protocols:
        return protocol_module.StepProtocolCustom(
            name=protocol_name,
            step_stimulus=step_stimuli[0],
            holding_stimulus=holding_stimulus,
            recordings=recordings,
            stochkv_det=stochkv_det,
        )
    elif protocol_module is sscx_protocols:
        return protocol_module.StepProtocol(
            name=protocol_name,
            step_stimuli=step_stimuli,
            holding_stimulus=holding_stimulus,
            recordings=recordings,
            stochkv_det=stochkv_det,
        )
    else:
        raise ValueError(f"unsupported protocol module: {protocol_module}")


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
