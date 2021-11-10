"""Functions to create recordings."""

from bluepyopt import ephys

from emodelrunner.synapses.recordings import SynapseRecordingCustom


def get_pairsim_recordings(
    soma_loc, syn_locs, synrecs, presyn_prot_name, postsyn_prot_name
):
    """Return the precell and the postcell recordings for a pair simulation.

    Args:
        soma_loc (bluepyopt.ephys.locations.NrnSeclistCompLocation):
            location of the soma of the pre-synaptic cell
        syn_locs (list of bluepyopt.ephys.locations.NrnPointProcessLocation):
            location of synapses  of the post-synaptic cell
        synrecs (list of str): the extra synapse variables to record
        presyn_prot_name (str): presynaptic protocol name
        postsyn_prot_name (str): postsynaptic protocol name

    Returns:
        a tuple containing

        - list of recordings: presynaptic recordings
        - list of recordings: postsynaptic recordings
    """
    presyn_rec = ephys.recordings.CompRecording(
        name=presyn_prot_name, location=soma_loc, variable="v"
    )
    presyn_recs = [presyn_rec]
    postsyn_rec = ephys.recordings.CompRecording(
        name=postsyn_prot_name, location=soma_loc, variable="v"
    )
    postsyn_recs = [postsyn_rec]

    for syn_loc in syn_locs:
        for synrec in synrecs:
            postsyn_recs.append(
                SynapseRecordingCustom(name=synrec, location=syn_loc, variable=synrec)
            )

    return (presyn_recs, postsyn_recs)
