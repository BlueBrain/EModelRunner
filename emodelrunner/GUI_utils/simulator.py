"""Class containing simulation for the GUI."""

import os
import numpy as np

from bluepyopt import ephys

from emodelrunner.recordings import RecordingCustom
from emodelrunner.cell import CellModelCustom
from emodelrunner.synapses.stimuli import NrnNetStimStimulusCustom
from emodelrunner.load import (
    load_config,
    load_syn_mechs,
    define_parameters,
    load_mechanisms,
    find_param_file,
    get_morph_args,
    get_release_params,
)
from emodelrunner.morphology import NrnFileMorphologyCustom, get_axon_hoc
from emodelrunner.synapses.create_locations import get_syn_locs


def section_coordinate_3d(sec, seg_pos):
    """Returns the 3d coordinate of a point in a section.

    Args:
        sec: neuron section
        seg_pos (float): postion of the segment os the section
            (should be between 0 and 1)
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


class NeuronSimulation:
    """Class containing BPO cell, simulation & protocol.

    Attributes:
        config (dict): dictionary containing configuration data
        cell_path (str): path to cell repo. should be "."
        total_duration (int): duration of cell simulation (ms)
        steps (list of floats): default step stimuli (mV)
        default_hypamp (float): default holding stimulus (mV)
        step_stim (float): selected step stimulus (mV)
        hypamp (float): selected holding stimulus (mV)
        step_delay (int): delay before applying step stimulus (ms)
        step_duration (int): duration of step stimulus (ms)
        hold_step_delay (int): delay of holding stimulus (ms)
        hold_step_duration (int): duration of holding stimulus (ms)
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

    def __init__(self, config_file=None):
        """Constructor. Load default params from config file."""
        # load config file
        self.config = load_config(filename=config_file)
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

    def load_protocol_params(self):
        """Load default protocol params."""
        self.total_duration = self.config.getint("Protocol", "total_duration")

        # step protocol params
        self.steps, self.default_hypamp = self.load_default_step_stim()
        self.step_stim = self.steps[0]
        self.hypamp = self.default_hypamp

        self.step_delay = self.config.getint("Protocol", "stimulus_delay")
        self.step_duration = self.config.getint("Protocol", "stimulus_duration")
        self.hold_step_delay = self.config.getint("Protocol", "hold_stimulus_delay")
        self.hold_step_duration = self.config.getint(
            "Protocol", "hold_stimulus_duration"
        )

    def load_synapse_params(self):
        """Load default synapse params."""
        # mtypes to be chosen from {mtypeidx: mtype_name, ...}
        self.available_pre_mtypes = self.load_available_pre_mtypes()
        # mtypes to be loaded [mtypeidx, ...]
        self.pre_mtypes = []
        # synapse netstim param depending on mtype {mtypeidx:[start, interval, number, noise]}
        self.netstim_params = {}

        # default synapse params
        self.syn_start = self.config.getint("Protocol", "syn_start")
        self.syn_interval = self.config.getint("Protocol", "syn_interval")
        self.syn_nmb_of_spikes = self.config.getint("Protocol", "syn_nmb_of_spikes")
        self.syn_noise = self.config.getint("Protocol", "syn_noise")

    def load_available_pre_mtypes(self):
        """Load the list of pre mtype cells to which are connected the synapses."""
        mtype_path = os.path.join(
            self.config.get("Paths", "syn_dir"),
            self.config.get("Paths", "syn_mtype_map"),
        )
        with open(mtype_path, "r") as mtype_file:
            raw_mtypes = mtype_file.readlines()

        # mtypes[id] = m-type name
        mtypes = {}
        for line in raw_mtypes:
            line = line.rstrip().split()
            if line:
                mtypes[int(line[0])] = line[1]

        return mtypes

    def load_default_step_stim(self):
        """Load the default step & holding stimuli."""
        amplitudes = [
            self.config.get("Protocol", "stimulus_amp1"),
            self.config.get("Protocol", "stimulus_amp2"),
            self.config.get("Protocol", "stimulus_amp3"),
        ]
        hypamp = self.config.get("Protocol", "hold_amp")

        return amplitudes, hypamp

    def get_syn_stim(self):
        """Create syanpse stimuli."""
        if self.pre_mtypes:
            syn_locs = get_syn_locs(self.cell)
            syn_total_duration = self.total_duration
            return NrnNetStimStimulusCustom(syn_locs, syn_total_duration)
        return None

    def load_protocol(self, protocol_name="protocol"):
        """Load BPO protocol."""
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
        """Create a cell. Returns cell, release params and time step."""
        # pylint: disable=too-many-locals
        emodel = self.config.get("Cell", "emodel")
        gid = self.config.getint("Cell", "gid")

        # load mechanisms
        recipes_path = "/".join(
            (
                self.config.get("Paths", "recipes_dir"),
                self.config.get("Paths", "recipes_file"),
            ),
        )
        params_filepath = find_param_file(recipes_path, emodel)
        mechs = load_mechanisms(params_filepath)

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
        # -> do not need to reload syn data each time user toggle synapse checkbox
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
        params = define_parameters(params_filepath)

        # load morphology
        morph_config = get_morph_args(self.config)
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
        self.release_params = get_release_params(self.config.get("Cell", "emodel"))
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
        """Returns voltage response."""
        responses = {
            recording.name: recording.response for recording in self.protocol.recordings
        }
        key = list(responses.keys())[0]
        resp = responses[key]
        return np.array(resp["time"]), np.array(resp["voltage"])
