"""Json utilities."""

import json

import numpy as np


class NpEncoder(json.JSONEncoder):
    """Class to encode numpy object as python object."""

    def default(self, o):
        """Convert numpy integer to int."""
        if isinstance(o, np.integer):
            return int(o)
        elif isinstance(o, np.floating):
            return float(o)
        elif isinstance(o, np.ndarray):
            return o.tolist()
        else:
            return super(NpEncoder, self).default(o)
