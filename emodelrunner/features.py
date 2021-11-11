"""Feature-related classes."""

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

from bluepyopt.ephys.efeatures import eFELFeature

logger = logging.getLogger(__name__)


def get_feature(
    feature_config,
    main_protocol,
    protocol_name,
    recording_name,
    prefix,
):
    """Return feature name and eFelFeature.

    Args:
        feature_config (dict): contains the feature-related config data
        main_protocol (RatSSCxMainProtocol): Main Protocol containing all the protocols
        protocol_name (str): name of the protocol used
        recording_name (str): name of the recording. used to get the trace
        prefix (str): prefix used in naming responses, features, recordings, etc.

    Returns:
        (str, bluepyopt.ephys.efeatures.eFELFeature): feature name, feature
    """
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

    feature = eFELFeature(
        feature_name,
        efel_feature_name=efel_feature_name,
        recording_names=recording_names,
        stim_start=stim_start,
        stim_end=stim_end,
        exp_mean=meanstd[0],
        exp_std=meanstd[1],
        stimulus_current=stimulus_current,
        threshold=threshold,
        int_settings={"strict_stiminterval": strict_stim},
    )

    return feature_name, feature


def define_efeatures(main_protocol, features_path, prefix=""):
    """Define the efeatures.

    Args:
        main_protocol (RatSSCxMainProtocol): Main Protocol containing all the protocols
        features_path (str): path to features file
        prefix (str): prefix used in naming responses, features, recordings, etc.

    Returns:
        dict: efeatures
    """
    with open(features_path, "r", encoding="utf-8") as features_file:
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
