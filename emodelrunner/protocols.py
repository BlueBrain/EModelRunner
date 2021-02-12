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


def get_syn_stim(syn_locs, syn_args):
    """Get synapse stimulus depending on mode."""
    if syn_args["syn_stim_mode"] == "vecstim" and syn_args["vecstim_random"] not in [
        "python",
        "neuron",
    ]:
        logger.warning(
            "vecstim random not set to 'python' nor to 'neuron' in config file."
        )
        logger.warning("vecstim random will be re-set to 'python'.")
        syn_args["vecstim_random"] = "python"

    if syn_args["syn_stim_mode"] == "netstim":
        return NrnNetStimStimulusCustom(
            syn_locs,
            syn_args["netstim_total_duration"],
            syn_args["syn_nmb_of_spikes"],
            syn_args["syn_interval"],
            syn_args["syn_start"],
            syn_args["syn_noise"],
        )
    if syn_args["syn_stim_mode"] == "vecstim":
        return NrnVecStimStimulusCustom(
            syn_locs,
            syn_args["syn_start"],
            syn_args["syn_stop"],
            syn_args["syn_stim_seed"],
            syn_args["vecstim_random"],
        )
    else:
        return 0


def get_step_numbers(run_all_steps, run_step_number, step_number=3):
    """Return the first and last step +1 to be run."""
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


def get_step_stimulus(step_args, amplitude, hypamp, soma_loc, syn_stim):
    """Return step, holding (and synapse) stimuli for one step amplitude."""
    # create step stimulus
    stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=amplitude,
        step_delay=step_args["step_delay"],
        step_duration=step_args["step_duration"],
        location=soma_loc,
        total_duration=step_args["total_duration"],
    )

    # create holding stimulus
    hold_stim = ephys.stimuli.NrnSquarePulse(
        step_amplitude=hypamp,
        step_delay=step_args["hold_step_delay"],
        step_duration=step_args["hold_step_duration"],
        location=soma_loc,
        total_duration=step_args["total_duration"],
    )

    # return stims
    stims = [stim, hold_stim]
    if syn_stim is not None:
        stims.append(syn_stim)
    return stims


def step_stimuli(
    amps_path,
    step_args,
    soma_loc,
    cvode_active=False,
    syn_stim=None,
):
    """Create Step Stimuli and return the Protocols for all stimuli."""
    # pylint: disable=too-many-locals
    # get current amplitude data
    amplitudes, hypamp = load_amps(amps_path)

    # get step numbers to run
    from_step, up_to = get_step_numbers(
        step_args["run_all_steps"], step_args["run_step_number"]
    )

    # protocol names
    protocol_names = ["step{}".format(x) for x in range(1, 4)]

    step_protocols = []
    for protocol_name, amplitude in zip(
        protocol_names[from_step:up_to], amplitudes[from_step:up_to]
    ):
        # use RecordingCustom to sample time, voltage every 0.1 ms.
        rec = RecordingCustom(name=protocol_name, location=soma_loc, variable="v")

        stims = get_step_stimulus(step_args, amplitude, hypamp, soma_loc, syn_stim)

        protocol = ephys.protocols.SweepProtocol(
            protocol_name, stims, [rec], cvode_active
        )

        step_protocols.append(protocol)

    return step_protocols


def define_protocols(
    step_args, syn_args, step_stim, add_synapses, amps_path, cvode_active, cell=None
):
    """Define Protocols."""
    # synapses location and stimuli
    if add_synapses and syn_args["syn_stim_mode"] in ["vecstim", "netstim"]:
        if cell is not None:
            # locations
            syn_locs = get_syn_locs(cell)
            # get synpase stimuli
            syn_stim = get_syn_stim(syn_locs, syn_args)
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
        protocols = step_stimuli(amps_path, step_args, soma_loc, cvode_active, syn_stim)
    elif syn_stim:
        protocol_name = syn_args["syn_stim_mode"]
        # use RecordingCustom to sample time, voltage every 0.1 ms.
        rec = RecordingCustom(name=protocol_name, location=soma_loc, variable="v")

        stims = [syn_stim]
        protocol = ephys.protocols.SweepProtocol(
            protocol_name, stims, [rec], cvode_active
        )
        protocols = [protocol]
    else:
        raise Exception(
            "No valid protocol was found. step_stimulus is {}".format(step_stim)
            + " and syn_stim_mode ({}) not in ['vecstim', 'netstim'].".format(
                syn_args["syn_stim_mode"]
            )
        )

    return ephys.protocols.SequenceProtocol("twostep", protocols=protocols)
