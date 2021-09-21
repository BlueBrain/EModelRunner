"""Functions to create stimuli."""
import os

import json

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
