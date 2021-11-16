"""Computation of morphology features."""

# Copyright 2020-2021 Blue Brain Project / EPFL

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import neurom as nm

logger = logging.getLogger(__name__)


class MorphologyFeature(object):
    """Morphology feature representation.

    Attributes:
        name (str): name of the feature
        value (float or list): value of the feature
        unit (str): unit of the feature
    """

    def __init__(self):
        """Sets initial attribute values."""
        self.name = None
        self.value = None
        self.unit = None

    @staticmethod
    def replace_empty_value(value):
        """Replaces the empty value with 0 or [0].

        Attrs:
            value (float or list): the value to be replaced if empty

        Returns:
            float/int or non-empty list
        """
        if value is None:
            value = 0
        elif hasattr(value, "len") and len(value) == 0:
            value = [0]
        return value

    def to_dict(self):
        """Returns a dictionary from the fields."""
        return self.__dict__


class TotalLength(MorphologyFeature):
    """Total length feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

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


class TotalHeight(MorphologyFeature):
    """Total height feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(TotalHeight, self).__init__()
        self.name = f"total {neurite_name} height"
        self.unit = "\u00b5m"
        feature_value = nm.get("total_height", morphology, neurite_type=neurite_type)
        self.value = self.replace_empty_value(feature_value)


class TotalWidth(MorphologyFeature):
    """Total width feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(TotalWidth, self).__init__()
        self.name = f"total {neurite_name} width"
        self.unit = "\u00b5m"
        feature_value = nm.get("total_width", morphology, neurite_type=neurite_type)
        self.value = self.replace_empty_value(feature_value)


class TotalDepth(MorphologyFeature):
    """Total depth feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(TotalDepth, self).__init__()
        self.name = f"total {neurite_name} depth"
        self.unit = "\u00b5m"
        feature_value = nm.get("total_depth", morphology, neurite_type=neurite_type)
        self.value = self.replace_empty_value(feature_value)


class TotalArea(MorphologyFeature):
    """Total area feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(TotalArea, self).__init__()
        self.name = f"total {neurite_name} area"
        self.unit = "\u00b5m\u00b2"
        feature_value = nm.get("total_area", morphology, neurite_type=neurite_type)
        self.value = self.replace_empty_value(feature_value)


class TotalVolume(MorphologyFeature):
    """Total volume feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(TotalVolume, self).__init__()
        self.name = f"total {neurite_name} volume"
        self.unit = "\u00b5m\u00b3"
        feature_value = nm.get("total_volume", morphology, neurite_type=neurite_type)
        self.value = self.replace_empty_value(feature_value)


class NumberOfSections(MorphologyFeature):
    """Number of sections feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(NumberOfSections, self).__init__()
        self.name = f"number of {neurite_name} sections"
        self.unit = ""
        feature_value = nm.get("number_of_sections", morphology, neurite_type=neurite_type)
        self.value = self.replace_empty_value(feature_value)


class MeanNeuriteVolumes(MorphologyFeature):
    """Total neurite volume feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

    def __init__(self, morphology, neurite_name, neurite_type):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
            neurite_name (str): neurite name, e.g. axon
            neurite_type (NeuriteType): enum for neurite type encoding
        """
        super(MeanNeuriteVolumes, self).__init__()
        self.name = f"mean {neurite_name} volume"
        self.unit = "\u00b5m\u00b3"
        feature_values = nm.get(
            "total_volume_per_neurite", morphology, neurite_type=neurite_type
        )
        feature_values = self.replace_empty_value(feature_values)
        self.value = sum(feature_values) / len(feature_values)


class MaxBranchOrder(MorphologyFeature):
    """Maximum branch order feature.

    Attributes:
        name (str): name of the feature
        value (int): value of the feature
        unit (str): unit of the feature
    """

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
    """Maximum section length feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

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
    """Soma diameter feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

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


class SomaSurfaceArea(MorphologyFeature):
    """Soma surface area feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

    def __init__(self, morphology):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
        """
        super(SomaSurfaceArea, self).__init__()
        self.name = "soma surface area"
        self.unit = "\u00b5m\u00b2"
        feature_value = nm.get("soma_surface_area", morphology)
        self.value = self.replace_empty_value(feature_value)


class SomaVolume(MorphologyFeature):
    """Soma volume feature.

    Attributes:
        name (str): name of the feature
        value (float): value of the feature
        unit (str): unit of the feature
    """

    def __init__(self, morphology):
        """Constructor.

        Args:
            morphology (neurom neuron object): morphology object
        """
        super(SomaVolume, self).__init__()
        self.name = "soma volume"
        self.unit = "\u00b5m\u00b3"
        feature_value = nm.get("soma_volume", morphology)
        self.value = self.replace_empty_value(feature_value)


class MorphologyFactsheetBuilder:
    """Computes the factsheet values for a morphology.

    Attributes:
        morphology (neurom.core.morphology.Morphology): morphology of the neuron
        neurite_names (str): names of the neurites types
        neurite_types (neurom type): the neurite types
    """

    def __init__(self, morph_path):
        """Load the morphology.

        Args:
            morph_path (str or Path): Path to the morphology file.
        """
        self.morphology = nm.load_morphology(morph_path)
        self.neurite_names, self.neurite_types = self.get_neurites()

    def get_neurites(self):
        """Return neurite names (str) and types (neurom type).

        If basal or apical are not present, name them 'dendrite'.

        Returns:
            tuple containing

            - list of str: neurite names
            - list of neurom type: neurite types
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

    def get_sscx_feature_values(self):
        """Returns the values of all features in a list."""
        all_values = []
        for neurite_name, neurite_type in zip(self.neurite_names, self.neurite_types):
            total_length = TotalLength(self.morphology, neurite_name, neurite_type)
            all_values.append(total_length.to_dict())

            volume = MeanNeuriteVolumes(self.morphology, neurite_name, neurite_type)
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
