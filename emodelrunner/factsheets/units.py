"""Contains the units of the features used in factsheets."""
from types import MappingProxyType
from efel.units import _units as efel_units

feature_units = efel_units.copy()

# add the bluepyopt units
feature_units["bpo_holding_current"] = "nA"
feature_units["bpo_threshold_current"] = "nA"

# make feature_units immutable
feature_units = MappingProxyType(feature_units)
