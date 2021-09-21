"""Feature-related classes."""

import json
import logging
import numpy

from bluepyopt.ephys.efeatures import eFELFeature
import efel

logger = logging.getLogger(__name__)


class eFELFeatureCustom(eFELFeature):
    """EFEL feature able to return bpo internal feature in calculate_feature."""

    SERIALIZED_FIELDS = (
        "name",
        "efel_feature_name",
        "recording_names",
        "stim_start",
        "stim_end",
        "exp_mean",
        "exp_std",
        "threshold",
        "comment",
    )

    def __init__(
        self,
        name,
        efel_feature_name=None,
        recording_names=None,
        stim_start=None,
        stim_end=None,
        exp_mean=None,
        exp_std=None,
        threshold=None,
        stimulus_current=None,
        comment="",
        interp_step=None,
        double_settings=None,
        int_settings=None,
        prefix="",
    ):
        """Constructor.

        Args:
            name (str): name of the eFELFeature object
            efel_feature_name (str): name of the eFeature in the eFEL library
                (ex: 'AP1_peak')
            recording_names (dict): eFEL features can accept several recordings
                as input
            stim_start (float): stimulation start time (ms)
            stim_end (float): stimulation end time (ms)
            exp_mean (float): experimental mean of this eFeature
            exp_std (float): experimental standard deviation of this eFeature
            threshold (float): spike detection threshold (mV)
            stimulus_current (float): amplitude of stimulus current (nA)
            comment (str): comment
            interp_step (float): interpolation step (ms)
            double_settings (dict): eFel double settings
            int_settings (dict): eFel int settings
            prefix (str): prefix used in naming responses, features, recordings, etc.
        """
        # pylint: disable=too-many-arguments, too-many-locals
        super(eFELFeatureCustom, self).__init__(
            name,
            efel_feature_name,
            recording_names,
            stim_start,
            stim_end,
            exp_mean,
            exp_std,
            threshold,
            stimulus_current,
            comment,
            interp_step,
            double_settings,
            int_settings,
        )

        self.prefix = prefix

    def get_bpo_feature(self, responses):
        """Return internal feature which is directly passed as a response.

        An internal feature is e.g. bpo_holding_current or bpo_threshold_current.
        They are not produced by eFel, but by BluePyOpt.
        """
        if (self.prefix + "." + self.efel_feature_name) not in responses:
            raise KeyError(
                f"Internal BluePyOpt feature {self.efel_feature_name} not set"
            )
        return responses[self.prefix + "." + self.efel_feature_name]

    def calculate_features(self, responses, raise_warnings=False):
        """Calculate feature value."""
        if self.efel_feature_name.startswith("bpo_"):  # check if internal feature
            try:
                feature_values = numpy.array(self.get_bpo_feature(responses))
            except KeyError:
                feature_values = None
        else:
            efel_trace = self._construct_efel_trace(responses)

            if efel_trace is None:
                feature_values = None
            else:
                self._setup_efel()

                values = efel.getFeatureValues(
                    [efel_trace],
                    [self.efel_feature_name],
                    raise_warnings=raise_warnings,
                )

                feature_values = values[0][self.efel_feature_name]

                efel.reset()

        logger.debug("Calculated values for %s: %s", self.name, str(feature_values))

        return feature_values


def get_feature(
    feature_config,
    main_protocol,
    protocol_name,
    recording_name,
    prefix,
):
    """Return eFelFeatureCustom and feature name."""
    # pylint: disable=too-many-locals
    efel_feature_name = feature_config["feature"]
    meanstd = feature_config["val"]

    if hasattr(main_protocol, "subprotocols"):
        protocol = main_protocol.subprotocols()[protocol_name]
    else:
        protocol = main_protocol[protocol_name]

    feature_name = f"{prefix}.{protocol_name}.{recording_name}.{efel_feature_name}"
    recording_names = {"": f"{prefix}.{protocol_name}.{recording_name}"}

    if "strict_stim" in feature_config:
        strict_stim = feature_config["strict_stim"]
    else:
        strict_stim = True

    if hasattr(protocol, "stim_start"):

        stim_start = protocol.stim_start

        if "threshold" in feature_config:
            threshold = feature_config["threshold"]
        else:
            threshold = -30

        if "bAP" in protocol_name:
            # bAP response can be after stimulus
            stim_end = protocol.total_duration
        elif "H40S8" in protocol_name:
            stim_end = protocol.stim_last_start
        else:
            stim_end = protocol.stim_end

        stimulus_current = protocol.step_amplitude

    else:
        stim_start = None
        stim_end = None
        stimulus_current = None
        threshold = None

    feature = eFELFeatureCustom(
        feature_name,
        efel_feature_name=efel_feature_name,
        recording_names=recording_names,
        stim_start=stim_start,
        stim_end=stim_end,
        exp_mean=meanstd[0],
        exp_std=meanstd[1],
        stimulus_current=stimulus_current,
        threshold=threshold,
        prefix=prefix,
        int_settings={"strict_stiminterval": strict_stim},
    )

    return feature_name, feature


def define_efeatures(main_protocol, features_filename, prefix=""):
    """Define the efeatures."""
    with open(features_filename, "r", encoding="utf-8") as features_file:
        feature_definitions = json.load(features_file)

    if "__comment" in feature_definitions:
        del feature_definitions["__comment"]

    efeatures = {}

    for protocol_name, locations in feature_definitions.items():
        for recording_name, feature_configs in locations.items():
            for feature_config in feature_configs:

                feature_name, feature = get_feature(
                    feature_config,
                    main_protocol,
                    protocol_name,
                    recording_name,
                    prefix,
                )
                efeatures[feature_name] = feature

    return efeatures
