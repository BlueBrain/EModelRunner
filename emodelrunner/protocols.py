"""Protocol creation functions."""

import logging

import bluepyopt.ephys as ephys

from emodelrunner.recordings import RecordingCustom
from emodelrunner.synapse import (
    NrnNetStimStimulusCustom,
    NrnVecStimStimulusCustom,
)
from emodelrunner.load import load_amps

logger = logging.getLogger(__name__)


def get_syn_locs(cell):
    """Load synapse point process location."""
    syn_locs = []
    for mech in cell.mechanisms:
        if hasattr(mech, "pprocesses"):
            syn_locs.append(
                ephys.locations.NrnPointProcessLocation("synapse_locs", mech)
            )

    if not syn_locs:
        syn_locs = None

    return syn_locs


def get_syn_stim(syn_locs, config, syn_stim_mode):
    """Get synapse stimulus depending on mode."""
    # load config data
    netstim_total_duration = config.getint("Protocol", "total_duration")
    syn_stop = config.getint("Protocol", "syn_stop")
    syn_interval = config.getint("Protocol", "syn_interval")
    syn_nmb_of_spikes = config.getint("Protocol", "syn_nmb_of_spikes")
    syn_start = config.getint("Protocol", "syn_start")
    syn_noise = config.getint("Protocol", "syn_noise")
    syn_stim_seed = config.getint("Protocol", "syn_stim_seed")
    vecstim_random = config.get("Protocol", "vecstim_random")

    if syn_stim_mode == "vecstim" and vecstim_random not in [
        "python",
        "neuron",
    ]:
        logger.warning(
            "vecstim random not set to 'python' nor to 'neuron' in config file."
        )
        logger.warning("vecstim random will be re-set to 'python'.")
        vecstim_random = "python"

    if syn_stim_mode == "netstim":
        return NrnNetStimStimulusCustom(
            syn_locs,
            netstim_total_duration,
            syn_nmb_of_spikes,
            syn_interval,
            syn_start,
            syn_noise,
        )
    if syn_stim_mode == "vecstim":
        return NrnVecStimStimulusCustom(
            syn_locs,
            syn_start,
            syn_stop,
            syn_stim_seed,
            vecstim_random,
        )
    else:
        return 0


def get_step_numbers(config, step_number=3):
    """Return the first and last step +1 to be run."""
    run_all_steps = config.getboolean("Protocol", "run_all_steps")
    run_step_number = config.getint("Protocol", "run_step_number")

    if run_all_steps:
        return 0, step_number
    elif run_step_number in range(1, step_number + 1):
        return run_step_number - 1, run_step_number
    else:
        logger.warning(
            " ".join(
                (
                    "Bad run_step_number parameter.",
                    "Should be between 1 and {}.".format(step_number),
                    "Only first step will be run.",
                )
            )
        )
        return 0, 1


def get_step_stimulus(config, amplitude, hypamp, soma_loc, syn_stim):
    """Return step, holding (and synapse) stimuli for one step amplitude."""
    # load config data
    total_duration = config.getint("Protocol", "total_duration")
    step_delay = config.getint("Protocol", "stimulus_delay")
    step_duration = config.getint("Protocol", "stimulus_duration")
    hold_step_delay = config.getint("Protocol", "hold_stimulus_delay")
    hold_step_duration = config.getint("Protocol", "hold_stimulus_duration")

    # create step stimulus
    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=amplitude,
        step_delay=step_delay,
        step_duration=step_duration,
        location=soma_loc,
        total_duration=total_duration,
    )

    # create holding stimulus
    hold_stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=hypamp,
        step_delay=hold_step_delay,
        step_duration=hold_step_duration,
        location=soma_loc,
        total_duration=total_duration,
    )

    # return stims
    stims = [stim, hold_stim]
    if syn_stim is not None:
        stims.append(syn_stim)
    return stims


def step_stimuli(config, soma_loc, cvode_active=False, syn_stim=None):
    """Create Step Stimuli and return the Protocols for all stimuli."""
    # get current amplitude data
    amplitudes, hypamp = load_amps(config)

    from_step, up_to = get_step_numbers(config)

    # protocol names
    protocol_names = ["step{}".format(x) for x in range(1, 4)]

    step_protocols = []
    for protocol_name, amplitude in zip(
        protocol_names[from_step:up_to], amplitudes[from_step:up_to]
    ):
        # use RecordingCustom to sample time, voltage every 0.1 ms.
        rec = RecordingCustom(name=protocol_name, location=soma_loc, variable="v")

        stims = get_step_stimulus(config, amplitude, hypamp, soma_loc, syn_stim)

        protocol = ephys.protocols.SweepProtocol(
            protocol_name, stims, [rec], cvode_active
        )

        step_protocols.append(protocol)

    return step_protocols


def define_protocols(config, cell=None):
    """Define Protocols."""
    # load config
    cvode_active = config.getboolean("Sim", "cvode_active")
    step_stim = config.getboolean("Protocol", "step_stimulus")
    add_synapses = config.getboolean("Synapses", "add_synapses")
    syn_stim_mode = config.get("Protocol", "syn_stim_mode")

    # synapses location and stimuli
    if add_synapses and syn_stim_mode in ["vecstim", "netstim"]:
        if cell is not None:
            # locations
            syn_locs = get_syn_locs(cell)
            # get synpase stimuli
            syn_stim = get_syn_stim(syn_locs, config, syn_stim_mode)
        else:
            raise Exception("The cell is  missing in the define_protocol function.")
    else:
        syn_stim = None

    # recording location
    soma_loc = ephys.locations.NrnSeclistCompLocation(
        name="soma", seclist_name="somatic", sec_index=0, comp_x=0.5
    )

    # get step stimuli and make protocol(s)
    if step_stim:
        # get step protocols
        step_protocols = step_stimuli(config, soma_loc, cvode_active, syn_stim)

    elif syn_stim:
        protocol_name = syn_stim_mode
        # use RecordingCustom to sample time, voltage every 0.1 ms.
        rec = RecordingCustom(name=protocol_name, location=soma_loc, variable="v")

        stims = [syn_stim]
        protocol = ephys.protocols.SweepProtocol(
            protocol_name, stims, [rec], cvode_active
        )
        step_protocols = [protocol]
    else:
        raise Exception(
            "No valid protocol was found. step_stimulus is {}".format(step_stim)
            + " and syn_stim_mode ({}) not in ['vecstim', 'netstim'].".format(
                syn_stim_mode
            )
        )

    return ephys.protocols.SequenceProtocol("twostep", protocols=step_protocols)
