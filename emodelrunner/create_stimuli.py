"""Functions to create stimuli."""

import json

from emodelrunner.stimuli import Pulse


# adapted from bglibpy.cell
def add_pulse(stimulus, soma_loc):
    """Return Pulse Stimulus.

    Args:
        stimulus (dict): contains the stimulus configuration data
        soma_loc (bluepyopt.ephys.locations.NrnSeclistCompLocation): location of the soma

    Returns:
        Pulse: pulse stimulus
    """
    return Pulse(
        location=soma_loc,
        delay=float(stimulus["Delay"]),
        duration=float(stimulus["Duration"]),
        amp=float(stimulus["AmpStart"]),
        frequency=float(stimulus["Frequency"]),
        width=float(stimulus["Width"]),
    )


def load_pulses(soma_loc, stim_path="protocols/stimuli.json"):
    """Return a list of pulse stimuli.

    Args:
        soma_loc (bluepyopt.ephys.locations.NrnSeclistCompLocation):
            location of the soma
        stim_path (str): path to the pulse stimuli file

    Raises:
        NotImplementedError: if stim["Pattern"] is not "Pulse" in simuli file

    Returns:
        list of Pulse stimuli
    """
    pulse_stims = []
    with open(stim_path, "r", encoding="utf-8") as f:
        stimuli = json.load(f)

    for _, stim in stimuli.items():
        if "Pattern" in stim and stim["Pattern"] == "Pulse":
            pulse_stims.append(add_pulse(stim, soma_loc))
        else:
            NotImplementedError(
                "Stimulus other than Pulse in stimuli file. Not implemented yet."
            )
    return pulse_stims
