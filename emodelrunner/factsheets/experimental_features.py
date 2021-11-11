"""Functionality to fetch the experimental features and parameters from the json files."""

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

logger = logging.getLogger(__name__)


def morphology_used_in_fitting(optimized_params_dict, emodel):
    """Returns the morphology name from finals.json used in model fitting.

    Args:
        optimized_params_dict (dict): contains the optimized parameters,
            as well as the original morphology path
        emodel (str): name of the emodel

    Returns:
        str: the original morphology name used in model fitting
    """
    emodel_params = optimized_params_dict[emodel]
    morph_path = emodel_params["morph_path"]
    morph_name = morph_path.split("/")[-1]
    return morph_name


def get_feature_dict(feature, units, morphology_prefix, stimulus, location, fitness):
    """Return dict containing one feature.

    Args:
        feature (dict): contains feature name and mean and std of feature
        units (dict): contains the units for the feature
        morphology_prefix (str): prefix used in the fitness key to the feature
        stimulus (str): name of the stimulus used for this feature
        location (str): name of the location for which the feature is calculated
        fitness (dict): contains the fitness of the feature

    Returns:
        dict containing name, values, unit and model fitness of the feature
    """
    feature_name = feature["feature"]
    mean = feature["val"][0]
    std = feature["val"][1]

    try:
        unit = units[feature_name]
    except KeyError:
        logger.warning(
            "%s was not found in units file. Setting unit to ''.", feature_name
        )
        unit = ""

    key_fitness = ".".join((morphology_prefix, stimulus, location, feature_name))
    try:
        fit = fitness[key_fitness]
    except KeyError:
        logger.warning(
            "%s was not found in fitness dict. Setting fitness model fitness value to ''.",
            key_fitness,
        )
        fit = ""

    return {
        "name": feature_name,
        "values": [{"mean": mean, "std": std}],
        "unit": unit,
        "model fitness": fit,
    }


def get_exp_features_data(
    emodel, morphology_prefix, features_dict, units, optimized_params_dict
):
    """Returns a dict containing mean and std of experimental features and model fitness.

    Args:
        emodel (str): name of the emodel
        morphology_prefix (str): prefix used in the fitness key to the feature
        features_dict (dict): contains the features
        units (dict): contains the units for the features
        optimized_params_dict (dict): contains the optimized parameters,
            as well as the original morphology path
    Returns:
        dict containing the output feature dicts and the original morph name used in model fitting
    """
    # pylint: disable=too-many-locals
    # it is hard to reduce number of locals without reducing readibility
    fitness = optimized_params_dict[emodel]["fitness"]

    values_dict = {}
    for stimulus, stim_data in features_dict.items():
        stim_dict = {}
        for location, loc_data in stim_data.items():
            features_list = []
            for feature in loc_data:
                features_list.append(
                    get_feature_dict(
                        feature, units, morphology_prefix, stimulus, location, fitness
                    )
                )
            loc_dict = {"features": features_list}
            stim_dict[location] = loc_dict
        values_dict[stimulus] = stim_dict
    values = [values_dict]

    fitted_morphology_name = morphology_used_in_fitting(optimized_params_dict, emodel)

    return {
        "name": "Experimental features",
        "values": values,
        "morphology": fitted_morphology_name,
    }
