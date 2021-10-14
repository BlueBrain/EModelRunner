"""Json utilities."""

import json

import numpy as np


class NpEncoder(json.JSONEncoder):
    """Class to encode numpy object as python object."""

    def default(self, o):
        """Convert numpy values to regular python values.

        Args:
            o: value to enventually convert if is a numpy object

        Returns:
            converted values or parent default method if not a numpy object
        """
        if isinstance(o, np.integer):
            return int(o)
        elif isinstance(o, np.floating):
            return float(o)
        elif isinstance(o, np.ndarray):
            return o.tolist()
        else:
            return super(NpEncoder, self).default(o)
