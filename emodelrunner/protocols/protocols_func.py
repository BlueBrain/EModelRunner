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

import logging

from bluepyopt import ephys

from emodelrunner.recordings import RecordingCustom
from emodelrunner.locations import SOMA_LOC


logger = logging.getLogger(__name__)

seclist_to_sec = {
    "somatic": "soma",
    "apical": "apic",
    "axonal": "axon",
    "myelinated": "myelin",
}


class CurrentOutputKeyMixin:
    """Contains methods useful for multiple Protocol classes."""

    def curr_output_key(self):
        """Get the output key for current based on the one for voltage.

        Returns:
            str used as key in current dict
        """
        if self.recordings is not None:
            # this gives 'prefix.name'
            name = ".".join(self.recordings[0].name.split(".")[:2])
        else:
            name = ""
        return "current_" + name


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
            location=SOMA_LOC,
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
