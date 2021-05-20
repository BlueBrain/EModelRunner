"""Functions to create synapse stimuli."""
import logging

from emodelrunner.synapses.stimuli import (
    NrnNetStimStimulusCustom,
    NrnVecStimStimulusCustom,
)

logger = logging.getLogger(__name__)


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
