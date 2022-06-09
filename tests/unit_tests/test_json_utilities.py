"""Unit tests for json_unitilies."""

import json
import numpy as np
from emodelrunner.json_utilities import NpEncoder


def test_np_encoder_array():
    """Unit test for the NpEncoder on np.array."""
    test_np_array = np.array([1, 2, 3])
    test_np_array_encoded = json.dumps(test_np_array, cls=NpEncoder)
    test_np_array_decoded = json.loads(test_np_array_encoded)
    assert test_np_array_decoded == test_np_array.tolist()

def test_np_encoder_integer():
    """Unit test for the NpEncoder on np.integer."""
    test_np_integer = np.int16(1)
    test_np_integer_encoded = json.dumps(test_np_integer, cls=NpEncoder)
    test_np_integer_decoded = json.loads(test_np_integer_encoded)
    assert test_np_integer_decoded == test_np_integer

def test_np_encoder_none():
    """Unit test for the NpEncoder on None."""
    test_np_none = None
    test_np_none_encoded = json.dumps(test_np_none, cls=NpEncoder)
    test_np_none_decoded = json.loads(test_np_none_encoded)
    assert test_np_none_decoded == test_np_none

def test_np_encoder_bool():
    """Unit test for the NpEncoder on bool."""
    test_np_bool = True
    test_np_bool_encoded = json.dumps(test_np_bool, cls=NpEncoder)
    test_np_bool_decoded = json.loads(test_np_bool_encoded)
    assert test_np_bool_decoded == test_np_bool