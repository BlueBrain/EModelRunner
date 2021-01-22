"""Function to load json files from inside package."""

import collections
import pkgutil

import json


def json_load(filepath):
    """Loads a json file from inside the package."""
    # path must be separated by '/'
    # returns a binary string
    json_bin_str = pkgutil.get_data("emodelrunner", filepath)

    # json loads cannot read binary so decode it beforehand.
    return json.loads(json_bin_str.decode(), object_pairs_hook=collections.OrderedDict)
