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
from emodelrunner.configuration import PackageType
from emodelrunner.protocols import synplas_protocols

from emodelrunner.synapses.recordings import SynapseRecordingCustom
from emodelrunner.stimuli import MultipleSteps
from emodelrunner.features import define_efeatures
from emodelrunner.protocols.reader import ProtocolParser
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
        """Constructor to be called by the classmethod overloads.

        Args:
            protocols (bluepyopt.ephys.protocols.SequenceProtocol): protocols to apply to the cell
        """
        self.protocols = protocols

    @staticmethod
    def _get_syn_locs(add_synapses, cell):
        """Wraps get_syn_locs with exception raising."""
        syn_locs = None
        if add_synapses:
            if cell is not None:
                syn_locs = get_syn_locs(cell)
            else:
                raise RuntimeError("'None' value encountered in cell object.")
        return syn_locs

    @classmethod
    def using_sscx_protocols(cls, add_synapses, prot_args, cell=None):
        """Creates the object with the sscx protocols.

        Args:
            add_synapses (bool): whether to add synapses to the cell
            prot_args (dict): config data relative to protocols
                See load.get_prot_args for details
            cell (CellModelCustom): cell model
        Returns:
            ProtocolBuilder: the object with the sscx protocols
        """
        syn_locs = cls._get_syn_locs(add_synapses, cell)

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
        Returns:
            ProtocolBuilder: the object with the thalamus protocols
        """
        syn_locs = cls._get_syn_locs(add_synapses, cell)

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

    def get_stim_currents(self, responses, dt):
        """Generates the currents injected by protocols.

        Args:
            responses (dict): the responses to the protocols run
            dt (float): timestep of the generated currents (ms)

        Returns:
            dict: the currents of the protocols.

            If the MainProtocol was used, only the RMP protocol,
            'pre-protocols' and 'other protocols' currents are returned
        """
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
                    threshold_current=thres_i, holding_current=hold_i, dt=dt
                )
            )

        return currents

    def get_thalamus_stim_currents(self, responses, mtype, dt):
        """Returns the currents injected by thalamus protocols.

        Args:
            responses (dict): protocol responses
            mtype (str): mtype to index the responses
            dt (float): timestep of the generated currents (ms)

        Returns:
            dict: the generated currents in a dict.
        """
        thres_i_hyp = responses[f"{mtype}.bpo_threshold_current_hyp"]
        thres_i_dep = responses[f"{mtype}.bpo_threshold_current_dep"]
        holding_i_hyp = responses[f"{mtype}.bpo_holding_current_hyp"]
        holding_i_dep = responses[f"{mtype}.bpo_holding_current_dep"]
        currents = {}
        for protocol in self.protocols.protocols:
            currents.update(
                protocol.generate_current(
                    thres_i_hyp, thres_i_dep, holding_i_hyp, holding_i_dep, dt
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

    Raises:
        ValueError: if the package type is not supported

    Returns:
        ephys.protocols.SequenceProtocol: sequence protocol containing all the protocols
    """
    # pylint: disable=unbalanced-tuple-unpacking, too-many-locals
    if package_type == PackageType.sscx:
        protocols_dict = ProtocolParser().parse_sscx_protocols(
            prot_path,
            stochkv_det,
            mtype,
            apical_point_isec,
            syn_locs,
        )
    elif package_type == PackageType.thalamus:
        protocols_dict = ProtocolParser().parse_thalamus_protocols(
            prot_path,
            stochkv_det,
            mtype,
        )
    else:
        raise ValueError(f"unsupported package type: {package_type}")

    if "Main" in protocols_dict:
        efeatures = define_efeatures(
            protocols_dict["Main"],
            features_path,
            mtype,
        )

        if package_type == PackageType.sscx:
            set_sscx_main_protocol_efeatures(protocols_dict, efeatures, prefix=mtype)
        elif package_type == PackageType.thalamus:
            set_thalamus_main_protocol_efeatures(
                protocols_dict, efeatures, prefix=mtype
            )

        protocols = [protocols_dict["Main"]]
    else:
        protocols = list(protocols_dict.values())

    return ephys.protocols.SequenceProtocol(
        "all protocols",
        protocols=protocols,
    )


def set_sscx_main_protocol_efeatures(protocols_dict, efeatures, prefix):
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


def set_thalamus_main_protocol_efeatures(protocols_dict, efeatures, prefix):
    """Set the efeatures of the main thalamus protocol.

    Args:
        protocols_dict (dict): contains all protocols to be run
            If this function is called, should contain the MainProtocol
            and the associated protocols (RinHoldCurrent, ThresholdDetection)
        efeatures (dict): contains the efeatures
        prefix (str): prefix used in naming responses, features, recordings, etc.
    """
    protocols_dict["Main"].rmp_efeature = efeatures[
        f"{prefix}.RMP.soma.v.steady_state_voltage_stimend"
    ]

    try:
        protocols_dict["Main"].rin_efeature_dep = efeatures[
            f"{prefix}.Rin_dep.soma.v.ohmic_input_resistance_vb_ssse"
        ]
    except KeyError:
        pass
    try:
        protocols_dict["Main"].rin_efeature_dep.stimulus_current = protocols_dict[
            "Main"
        ].rinhold_protocol_dep.rin_protocol_template.step_stimulus.step_amplitude
    except AttributeError:
        pass

    protocols_dict["Main"].rin_efeature_hyp = efeatures[
        f"{prefix}.Rin_hyp.soma.v.ohmic_input_resistance_vb_ssse"
    ]

    protocols_dict["Main"].rin_efeature_hyp.stimulus_current = protocols_dict[
        "Main"
    ].rinhold_protocol_hyp.rin_protocol_template.step_stimulus.step_amplitude

    try:
        protocols_dict["RinHoldcurrent_dep"].voltagebase_efeature = efeatures[
            f"{prefix}.Rin_dep.soma.v.voltage_base"
        ]
        protocols_dict["ThresholdDetection_dep"].holding_voltage = efeatures[
            f"{prefix}.Rin_dep.soma.v.voltage_base"
        ].exp_mean

    except KeyError:
        pass
    protocols_dict["RinHoldcurrent_hyp"].voltagebase_efeature = efeatures[
        f"{prefix}.Rin_hyp.soma.v.voltage_base"
    ]
    protocols_dict["ThresholdDetection_hyp"].holding_voltage = efeatures[
        f"{prefix}.Rin_hyp.soma.v.voltage_base"
    ].exp_mean


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
