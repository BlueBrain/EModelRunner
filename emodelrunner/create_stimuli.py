"""Functions to create stimuli."""
import os

import json
import numpy as np

from bluepyopt import ephys
from emodelrunner.stimuli import Pulse


# adapted from bglibpy.cell
def add_pulse(stimulus, soma_loc):
    """Return Pulse Stimulus."""
    return Pulse(
        location=soma_loc,
        delay=float(stimulus["Delay"]),
        duration=float(stimulus["Duration"]),
        amp=float(stimulus["AmpStart"]),
        frequency=float(stimulus["Frequency"]),
        width=float(stimulus["Width"]),
    )


def load_pulses(soma_loc, stim_dir="protocols", stim_fname="stimuli.json"):
    """Return a list of pulse stimuli."""
    pulse_stims = []
    stim_path = os.path.join(stim_dir, stim_fname)
    with open(stim_path, "r", encoding="utf-8") as f:
        stimuli = json.load(f)

    for _, stim in stimuli.items():
        if stim["Pattern"] == "Pulse":
            pulse_stims.append(add_pulse(stim, soma_loc))
        else:
            NotImplementedError(
                "Stimulus other than Pulse in stimuli file. Not implemented yet."
            )
    return pulse_stims


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


def generate_current(
    total_duration, holding_current, stim_start, stim_end, amplitude, dt=0.1
):
    """Return current time series."""
    t = np.arange(0.0, total_duration, dt)
    current = np.full(t.shape, holding_current, dtype="float64")

    ton_idx = int(stim_start / dt)
    toff_idx = int(stim_end / dt)

    current[ton_idx:toff_idx] += amplitude

    return t, current
