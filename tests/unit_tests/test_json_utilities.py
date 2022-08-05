"""Unit tests for json_unitilies."""

import json
import numpy as np
from hypothesis.extra import numpy as hp_numpy
from hypothesis import given, strategies as st
from emodelrunner.json_utilities import NpEncoder


json_serializable_np_dtypes = (
    hp_numpy.integer_dtypes(),
    hp_numpy.unsigned_integer_dtypes(),
    hp_numpy.floating_dtypes(),
)


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


def test_np_encoder_float():
    """Unit test for the NpEncoder on float."""
    test_np_float = np.float32(1.0)
    test_np_float_encoded = json.dumps(test_np_float, cls=NpEncoder)
    test_np_float_decoded = json.loads(test_np_float_encoded)
    assert test_np_float_decoded == test_np_float


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


@given(
    hp_numpy.arrays(
        st.one_of(
            *json_serializable_np_dtypes,
            hp_numpy.array_dtypes(
                subtype_strategy=st.one_of(*json_serializable_np_dtypes)
            ),
        ),
        # limit array size to avoid memory error and long testing time
        st.integers(min_value=0, max_value=1000),
    )
)
def test_np_encoder_array_with_hp(test_np_array):
    """Unit test for the NpEncoder on np.array."""
    test_np_array_encoded = json.dumps(test_np_array, cls=NpEncoder)
    test_np_array_decoded = json.loads(test_np_array_encoded)
    assert np.array_equal(test_np_array_decoded, test_np_array.tolist(), equal_nan=True)
