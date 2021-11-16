"""Class containing simulation for the GUI."""

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
import os
import numpy as np

from bluepyopt import ephys

from emodelrunner.recordings import RecordingCustom
from emodelrunner.cell import CellModelCustom
from emodelrunner.synapses.stimuli import NrnNetStimStimulusCustom
from emodelrunner.load import (
    load_sscx_config,
    load_syn_mechs,
    load_unoptimized_parameters,
    load_mechanisms,
    get_sscx_morph_args,
    get_release_params,
)
from emodelrunner.morphology import NrnFileMorphologyCustom, get_axon_hoc
from emodelrunner.synapses.create_locations import get_syn_locs


def section_coordinate_3d(sec, seg_pos):
    """Returns the 3d coordinates of a point in a section.

    Args:
        sec: neuron section
        seg_pos (float): postion of the segment os the section
            (should be between 0 and 1)

    Returns:
        list: 3d coordinates of a point in a section, or None if not found
    """
    n3d = sec.n3d()

    arc3d = [sec.arc3d(i) for i in range(n3d)]
    x3d = [sec.x3d(i) for i in range(n3d)]
    y3d = [sec.y3d(i) for i in range(n3d)]
    z3d = [sec.z3d(i) for i in range(n3d)]

    if not arc3d or seg_pos < 0 or seg_pos > 1:
        return None

    seg_pos = seg_pos * arc3d[-1]

    if seg_pos in arc3d:
        idx = arc3d.index(seg_pos)
        local_x = x3d[idx]
        local_y = y3d[idx]
        local_z = z3d[idx]
        return [local_x, local_y, local_z]
    else:
        for i, arc in enumerate(arc3d[1:]):
            if arc > seg_pos > arc3d[i - 1] and arc - arc3d[i - 1] != 0:
                proportion = (seg_pos - arc3d[i - 1]) / (arc - arc3d[i - 1])
                local_x = x3d[i - 1] + proportion * (x3d[i] - x3d[i - 1])
                local_y = y3d[i - 1] + proportion * (y3d[i] - y3d[i - 1])
                local_z = z3d[i - 1] + proportion * (z3d[i] - z3d[i - 1])
                return [local_x, local_y, local_z]

    return None


def get_pos_and_color(sec, seg_pos, syn_type):
    """Returns the position and the synaptic type (0 for inhib. or 1 for excit.).

    Args:
        sec: neuron section
        seg_pos (float): postion of the segment os the section
            (should be between 0 and 1)
        syn_type (int): synaptic type. excitatory if >100,
            inhibitory if <100

    Returns:
        list: first 3 numbers are the position, fourth is the synaptic type, None if pos not found
    """
    pos = section_coordinate_3d(sec, seg_pos)

    if pos is None:
        return None

    if syn_type > 100:
        syn_type_ = 1
    else:
        syn_type_ = 0
    pos.append(syn_type_)

    return pos


def get_step_data(steps, step, default_step):
    """Extract step data from StepProtocol json dict and add amplitude to a step list.

    Args:
        steps (list): list of step amplitudes (nA) to be updated
        step (dict or list of dicts): step from which to extract step data
        default_step (float): default value for the custom step entry (nA)

    Returns:
        a tuple containing

        - float: total duration of the step (ms)
        - float: delay of the step (ms)
        - float: duration of the step (ms)
    """
    # can be dict or list of dicts
    if isinstance(step, list):
        for step_ in step:
            # If a default step amplitude is registered,
            # two buttons will have the same value:
            # the registered one and the custom one
            if step_["amp"] != default_step:
                steps.append(step_["amp"])

            # replace default values
            # may be replaced several times
            total_duration = step_["totduration"]
            step_delay = step_["delay"]
            step_duration = step_["duration"]
    else:
        if step["amp"] != default_step:
            steps.append(step["amp"])

        total_duration = step["totduration"]
        step_delay = step["delay"]
        step_duration = step["duration"]

    return total_duration, step_delay, step_duration


def get_holding_data(holdings, stimulus_data, total_duration, default_holding):
    """Extract holding data from StepProtocol json dict and add amplitude to a holding list.

    Args:
        holdings (list): list of holding amplitudes (nA) to be updated
        stimulus_data (dict): stimulus dict from protocol json file containing holding data
        total_duration (float): total duration of the step (ms)
        default_holding (float): default value for the custom holding entry

    Returns:
        a tuple containing

        - float: delay of the holding stimulus (ms)
        - float: duration of the holding stimulus (ms)
    """
    if "holding" in stimulus_data:
        holding = stimulus_data["holding"]

        # amp can be None in e.g. Rin recipe protocol
        if holding["amp"] is not None and holding["amp"] != default_holding:
            holdings.append(holding["amp"])

        hold_step_delay = holding["delay"]
        hold_step_duration = holding["duration"]
    else:
        hold_step_delay = 0.0
        hold_step_duration = total_duration

    return hold_step_delay, hold_step_duration


class NeuronSimulation:
    """Class containing BPO cell, simulation & protocol.

    Attributes:
        config (dict): dictionary containing configuration data
        cell_path (str): path to cell repo. should be "."
        total_duration (float): duration of cell simulation (ms)
        steps (list of floats): default step stimuli (nA)
        hypamps (list of floats): default holding stimuli (nA)
        step_stim (float): selected step stimulus (nA)
        hypamp (float): selected holding stimulus (nA)
        step_delay (float): delay before applying step stimulus (ms)
        step_duration (float): duration of step stimulus (ms)
        hold_step_delay (float): delay of holding stimulus (ms)
        hold_step_duration (float): duration of holding stimulus (ms)
        available_pre_mtypes (dict): all synapses pre_mtypes
            {mtypeidx: mtype_name, ...}
        pre_mtypes (list of int): selected pre_mtypes to run
            [mtypeidx, ...]
        netstim_params (dict): netstim parameters for synapses of each mtype
            {mtypeidx:[start, interval, number, noise]}
        syn_start (int): default time (ms) at which the synapse starts firing
        syn_interval (int): default interval (ms) between two synapse firing
        syn_nmb_of_spikes (int): default number of synapse firing
        syn_noise (int): default synapse noise
        protocol (ephys.protocols.SweepProtocol): BluePyOpt-based Protocol
        cell (CellModelCustom): BluePyOpt-based cell
        release_params (dict): optimised cell parameters to fill in
            the cell's free parameters
        sim (ephys.simulators.NrnSimulator): BluePyOpt simulator
            can access neuron data from it
        syn_display_data (dict): synapse data (position and type) for display
            syn_display_data[pre_mtype] = [x,y,z,type],
            type=0 if inhib, type=1 if excit
    """

    def __init__(self, config_path="config/config_allsteps.ini"):
        """Constructor. Load default params from config file.

        Args:
            config_path (str):path to the config file
        """
        # load config file
        self.config = load_sscx_config(config_path=config_path)
        self.cell_path = self.config.get("Paths", "memodel_dir")

        # get default params
        self.load_protocol_params()
        self.load_synapse_params()

        # uninstantiated params
        self.protocol = None
        self.cell = None
        self.release_params = None
        self.sim = None
        self.syn_display_data = None

    def load_protocol_params(
        self,
        total_duration=3000,
        step_delay=700,
        step_duration=2000,
        hold_step_delay=0,
        hold_step_duration=3000,
        default_step=0,
        default_holding=0,
    ):
        """Load default protocol params.

        Args:
            total_duration (float): default value for duration of cell simulation (ms)
                if no StepProtocol is found
            step_delay (float): default value for delay before applying step stimulus (ms)
                if no StepProtocol is found
            step_duration (float): default value for duration of step stimulus (ms)
                if no StepProtocol is found
            hold_step_delay (float): default value for delay of holding stimulus (ms)
                if no StepProtocol is found
            hold_step_duration (float): default value for duration of holding stimulus (ms)
                if no StepProtocol is found
            default_step (float): default value for custom step amplitude (nA)
            default_holding (float): default value for custom holding amplitude (nA)
        """
        prot_path = self.config.get("Paths", "prot_path")
        with open(prot_path, "r", encoding="utf-8") as protocol_file:
            protocol_data = json.load(protocol_file)
        if "__comment" in protocol_data:
            del protocol_data["__comment"]

        # list of all steps and hold amps found in all stepprotocols in prot file
        steps = []
        holdings = []

        for prot_data in protocol_data.values():
            # update default delays / durations and update steps and holdings lists
            if prot_data["type"] == "StepProtocol":
                total_duration, step_delay, step_duration = get_step_data(
                    steps=steps,
                    step=prot_data["stimuli"]["step"],
                    default_step=default_step,
                )

                hold_step_delay, hold_step_duration = get_holding_data(
                    holdings, prot_data["stimuli"], total_duration, default_holding
                )

        self.total_duration = total_duration

        # filter duplicates (dict preserves order for py37+)
        self.steps = list(dict.fromkeys(steps))
        self.hypamps = list(dict.fromkeys(holdings))

        # set default values for custom entry
        self.step_stim = default_step
        self.hypamp = default_holding

        self.step_delay = step_delay
        self.step_duration = step_duration
        self.hold_step_delay = hold_step_delay
        self.hold_step_duration = hold_step_duration

    def load_synapse_params(
        self, syn_start=0, syn_interval=0, syn_nmb_of_spikes=0, syn_noise=0
    ):
        """Load default synapse params.

        Args:
            syn_start (int): default time (ms) at which the synapse starts firing
            syn_interval (int): default interval (ms) between two synapse firing
            syn_nmb_of_spikes (int): default number of synapse firing
            syn_noise (int): default synapse noise
        """
        # mtypes to be chosen from {mtypeidx: mtype_name, ...}
        self.available_pre_mtypes = self.load_available_pre_mtypes()
        # mtypes to be loaded [mtypeidx, ...]
        self.pre_mtypes = []
        # synapse netstim param depending on mtype {mtypeidx:[start, interval, number, noise]}
        self.netstim_params = {}

        # default synapse params
        self.syn_start = syn_start
        self.syn_interval = syn_interval
        self.syn_nmb_of_spikes = syn_nmb_of_spikes
        self.syn_noise = syn_noise

    def load_available_pre_mtypes(self):
        """Load the list of pre mtype cells to which are connected the synapses.

        Returns:
            dict: mtypes of cells connected to the synapses
        """
        mtype_path = os.path.join(
            self.config.get("Paths", "syn_dir"),
            self.config.get("Paths", "syn_mtype_map"),
        )
        with open(mtype_path, "r", encoding="utf-8") as mtype_file:
            raw_mtypes = mtype_file.readlines()

        # mtypes[id] = m-type name
        mtypes = {}
        for line in raw_mtypes:
            line = line.rstrip().split()
            if line:
                mtypes[int(line[0])] = line[1]

        return mtypes

    def get_syn_stim(self):
        """Create syanpse stimuli.

        Returns:
            emodelrunner.synapses.stimuli.NrnNetStimStimulusCustom: synapse stimuli
        """
        if self.pre_mtypes:
            syn_locs = get_syn_locs(self.cell)
            syn_total_duration = self.total_duration
            return NrnNetStimStimulusCustom(syn_locs, syn_total_duration)
        return None

    def load_protocol(self, protocol_name="protocol"):
        """Load BPO protocol.

        Args:
            protocol_name (str): protocol name to use in BluePyOpt classes.
                Does not have an effect on the simulation
        """
        syn_stim = self.get_syn_stim()

        soma_loc = ephys.locations.NrnSeclistCompLocation(
            name="soma", seclist_name="somatic", sec_index=0, comp_x=0.5
        )

        rec = RecordingCustom(name=protocol_name, location=soma_loc, variable="v")

        # create step stimulus
        stim = ephys.stimuli.NrnSquarePulse(
            step_amplitude=self.step_stim,
            step_delay=self.step_delay,
            step_duration=self.step_duration,
            location=soma_loc,
            total_duration=self.total_duration,
        )

        # create holding stimulus
        hold_stim = ephys.stimuli.NrnSquarePulse(
            step_amplitude=self.hypamp,
            step_delay=self.hold_step_delay,
            step_duration=self.hold_step_duration,
            location=soma_loc,
            total_duration=self.total_duration,
        )

        # create protocol
        stims = [stim, hold_stim]
        if syn_stim is not None:
            stims.append(syn_stim)

        self.protocol = ephys.protocols.SweepProtocol(
            protocol_name, stims, [rec], False
        )

    def create_cell_custom(self):
        """Create a cell.

        Returns:
            emodelrunner.cell.CellModelCustom: cell model
        """
        # pylint: disable=too-many-locals
        emodel = self.config.get("Cell", "emodel")
        gid = self.config.getint("Cell", "gid")

        # load mechanisms
        unopt_params_path = self.config.get("Paths", "unoptimized_params_path")
        mechs = load_mechanisms(unopt_params_path)

        # add synapses mechs
        seed = self.config.getint("Synapses", "seed")
        rng_settings_mode = self.config.get("Synapses", "rng_settings_mode")
        syn_data_path = os.path.join(
            self.config.get("Paths", "syn_dir"),
            self.config.get("Paths", "syn_data_file"),
        )
        syn_conf_path = os.path.join(
            self.config.get("Paths", "syn_dir"),
            self.config.get("Paths", "syn_conf_file"),
        )
        # always load synapse data for synapse display.
        # -> do not need to reload syn data each time user toggles synapse checkbox
        mechs += [
            load_syn_mechs(
                seed,
                rng_settings_mode,
                syn_data_path,
                syn_conf_path,
                self.pre_mtypes,
                self.netstim_params,
            )
        ]

        # load parameters
        params = load_unoptimized_parameters(
            unopt_params_path,
            v_init=self.config.getfloat("Cell", "v_init"),
            celsius=self.config.getfloat("Cell", "celsius"),
        )

        # load morphology
        morph_config = get_sscx_morph_args(self.config)
        replace_axon_hoc = get_axon_hoc(morph_config["axon_hoc_path"])
        morph = NrnFileMorphologyCustom(
            morph_config["morph_path"],
            do_replace_axon=morph_config["do_replace_axon"],
            replace_axon_hoc=replace_axon_hoc,
        )

        # create cell
        cell = CellModelCustom(
            name=emodel,
            morph=morph,
            mechs=mechs,
            params=params,
            gid=gid,
        )

        return cell

    def load_cell_sim(self):
        """Load BPO cell & simulation."""
        self.cell = self.create_cell_custom()
        self.release_params = get_release_params(self.config)
        self.sim = ephys.simulators.NrnSimulator(
            dt=self.config.getfloat("Sim", "dt"), cvode_active=False
        )

    def load_synapse_display_data(self):
        """Load dict containing x,y,z of each synapse & inhib/excit."""
        # self.syn_display_data[pre_mtype] = [x,y,z,type], type=0 if inhib, type=1 if excit
        self.syn_display_data = {}
        for key in self.available_pre_mtypes:
            self.syn_display_data[key] = []

        for mech in self.cell.mechanisms:
            if hasattr(mech, "pprocesses"):
                for syn in mech.synapses_data:
                    pre_mtype = syn["pre_mtype"]
                    seg_pos = syn["seg_x"]
                    # check if a synapse of the same mtype has already the same position
                    # and add synapse only if a new position has to be displayed
                    syn_section = mech.get_cell_section_for_synapse(
                        syn, self.cell.icell
                    )
                    syn_display_data = get_pos_and_color(
                        syn_section, seg_pos, syn["synapse_type"]
                    )
                    if (
                        syn_display_data is not None
                        and syn_display_data not in self.syn_display_data[pre_mtype]
                    ):
                        self.syn_display_data[pre_mtype].append(syn_display_data)

    def instantiate(self):
        """Instantiate cell, simulation & protocol."""
        self.cell.freeze(self.release_params)
        self.cell.instantiate(sim=self.sim)
        self.protocol.instantiate(sim=self.sim, icell=self.cell.icell)
        self.sim.neuron.h.tstop = self.protocol.total_duration
        self.sim.neuron.h.stdinit()

    def destroy(self):
        """Destroy cell & protocol."""
        self.protocol.destroy(sim=self.sim)
        self.cell.destroy(sim=self.sim)
        self.cell.unfreeze(self.release_params.keys())

    def get_voltage(self):
        """Returns voltage response.

        Returns:
            a tuple containing

            - ndarray: the time response
            - ndarray: the voltage response
        """
        responses = {
            recording.name: recording.response for recording in self.protocol.recordings
        }
        key = list(responses.keys())[0]
        resp = responses[key]
        return np.array(resp["time"]), np.array(resp["voltage"])
