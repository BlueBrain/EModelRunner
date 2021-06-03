"""Json utilities."""

import collections
import pkgutil
import json

import numpy as np


def load_package_json(filepath):
    """Loads a json file from inside the package."""
    # path must be separated by '/'
    # returns a binary string
    json_bin_str = pkgutil.get_data("emodelrunner", filepath)

    # json loads cannot read binary so decode it beforehand.
    return json.loads(json_bin_str.decode(), object_pairs_hook=collections.OrderedDict)


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
