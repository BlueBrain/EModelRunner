"""Computation of morphology features."""

import logging
import neurom as nm

logger = logging.getLogger(__name__)


class MorphologyFeature(object):
    """Morphology feature representation."""

    def __init__(self):
        """Sets initial attribute values."""
        self.name = None
        self.value = None
        self.unit = None

    @staticmethod
    def replace_empty_value(value):
        """Replaces the empty value with 0 or [0]."""
        if value is None:
            value = 0
        elif hasattr(value, "len") and len(value) == 0:
            value = [0]
        return value

    def to_dict(self):
        """Returns a dictionary from the fields."""
        return self.__dict__


class TotalLength(MorphologyFeature):
    """Total length feature."""

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(TotalLength, self).__init__()
        self.name = f"total {neurite_name} length"
        self.unit = "\u00b5m"
        feature_value = nm.get("total_length", morphology, neurite_type=neurite_type)
        self.value = self.replace_empty_value(feature_value)


class NeuriteVolumes(MorphologyFeature):
    """Total neurite volume feature."""

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(NeuriteVolumes, self).__init__()
        self.name = f"mean {neurite_name} volume"
        self.unit = "\u00b5m\u00b3"
        feature_values = nm.get(
            "total_volume_per_neurite", morphology, neurite_type=neurite_type
        )
        feature_values = self.replace_empty_value(feature_values)
        self.value = sum(feature_values) / len(feature_values)


class MaxBranchOrder(MorphologyFeature):
    """Maximum branch order feature."""

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(MaxBranchOrder, self).__init__()
        self.name = f"{neurite_name} maximum branch order"
        self.unit = ""
        feature_values = nm.get(
            "section_branch_orders", morphology, neurite_type=neurite_type
        )
        feature_values = self.replace_empty_value(feature_values)
        self.value = max(feature_values)


class MaxSectionLength(MorphologyFeature):
    """Maximum section length feature."""

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(MaxSectionLength, self).__init__()
        self.name = f"{neurite_name} maximum section length"
        self.unit = "\u00b5m"
        feature_values = nm.get(
            "section_lengths", morphology, neurite_type=neurite_type
        )
        feature_values = self.replace_empty_value(feature_values)
        self.value = max(feature_values)


class SomaDiamater(MorphologyFeature):
    """Soma diameter feature."""

    def __init__(self, morphology):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
        """
        super(SomaDiamater, self).__init__()
        self.name = "soma diameter"
        self.unit = "\u00b5m"
        feature_value = nm.get("soma_radius", morphology)
        self.value = 2 * self.replace_empty_value(feature_value)


class MorphologyFactsheetBuilder:
    """Computes the factsheet values for a morphology."""

    def __init__(self, morph_path):
        """Load the morphology.

        Args:
            morph_path (str or Path): Path to the morphology file.
        """
        self.morphology = nm.load_neuron(morph_path)
        self.neurite_names, self.neurite_types = self.get_neurites()

    def get_neurites(self):
        """Return neurite names (str) and types (neurom type).

        If basal or apical are not present, name them 'dendrite'.
        """
        api = nm.get("total_length", self.morphology, neurite_type=nm.APICAL_DENDRITE)
        bas = nm.get("total_length", self.morphology, neurite_type=nm.BASAL_DENDRITE)
        if api and bas:
            return ["axon", "apical", "basal"], [
                nm.AXON,
                nm.APICAL_DENDRITE,
                nm.BASAL_DENDRITE,
            ]
        elif api and not bas:
            return ["axon", "dendrite"], [nm.AXON, nm.APICAL_DENDRITE]
        elif bas and not api:
            return ["axon", "dendrite"], [nm.AXON, nm.BASAL_DENDRITE]
        logger.warning("No dendrite found!")
        return ["axon"], [nm.AXON]

    def get_all_feature_values(self):
        """Returns the values of all features in a list."""
        all_values = []
        for neurite_name, neurite_type in zip(self.neurite_names, self.neurite_types):
            total_length = TotalLength(self.morphology, neurite_name, neurite_type)
            all_values.append(total_length.to_dict())

            volume = NeuriteVolumes(self.morphology, neurite_name, neurite_type)
            all_values.append(volume.to_dict())

            max_branch_order = MaxBranchOrder(
                self.morphology, neurite_name, neurite_type
            )
            all_values.append(max_branch_order.to_dict())

            max_section_length = MaxSectionLength(
                self.morphology, neurite_name, neurite_type
            )
            all_values.append(max_section_length.to_dict())

        soma_diam = SomaDiamater(self.morphology)
        all_values.append(soma_diam.to_dict())

        return all_values
