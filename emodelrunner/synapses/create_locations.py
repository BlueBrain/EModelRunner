"""Functions to create synapse locations."""
from bluepyopt import ephys


def get_syn_locs(cell):
    """Load synapse point process location.

    Args:
        cell (bluepyopt.ephys.models.CellModel): cell model containing the synapses

    Returns:
        list containing the synapse locations
    """
    syn_locs = []
    for mech in cell.mechanisms:
        if hasattr(mech, "pprocesses"):
            syn_locs.append(
                ephys.locations.NrnPointProcessLocation("synapse_locs", mech)
            )

    if not syn_locs:
        syn_locs = None

    return syn_locs
