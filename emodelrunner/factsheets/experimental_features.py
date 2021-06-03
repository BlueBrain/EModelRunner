"""Functionality to fetch the experimental features and parameters from the json files."""

import logging
from emodelrunner.json_utilities import load_package_json

logger = logging.getLogger(__name__)


def load_emodel_recipe_dict(recipes_path, emodel):
    """Get recipe dict."""
    recipes = load_package_json(recipes_path)

    return recipes[emodel]


def load_raw_exp_features(recipe):
    """Load experimental features from file."""
    features_path = recipe["features"]

    return load_package_json(features_path)


def load_feature_units():
    """Load dict with 'feature_name': 'unit' for all features."""
    unit_json_path = "/".join(("config", "features", "units.json"))

    return load_package_json(unit_json_path)


def load_emodel_fitness(params_path, emodel):
    """Load dict containing model fitness value for each feature."""
    params_file = load_package_json(params_path)
    emodel_params = params_file[emodel]
    return emodel_params["fitness"]


def load_morphology_used_in_fitting(params_path, emodel):
    """Loads the morphology from the finals.json used in model fitting."""
    params_file = load_package_json(params_path)
    emodel_params = params_file[emodel]
    morph_path = emodel_params["morph_path"]
    morph_name = morph_path.split("/")[-1]
    return morph_name


def get_morphology_prefix_from_recipe(recipe):
    """Get the morphology prefix from an emodel recipe (e.g. '_' or 'L5TPCa')."""
    return recipe["morphology"][0][0]


def get_feature_dict(feature, units, morphology_prefix, stimulus, location, fitness):
    """Return dict containing one feature."""
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


def get_exp_features_data(emodel, recipes_path, params_path):
    """Returns a dict containing mean and std of experimental features and model fitness."""
    # pylint: disable=too-many-locals
    # it is hard to reduce number of locals without reducing readibility
    recipe = load_emodel_recipe_dict(recipes_path, emodel)

    features_dict = load_raw_exp_features(recipe)
    units = load_feature_units()
    fitness = load_emodel_fitness(params_path, emodel)

    morphology_prefix = get_morphology_prefix_from_recipe(recipe)

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

    fitted_morphology_name = load_morphology_used_in_fitting(params_path, emodel)

    return {
        "name": "Experimental features",
        "values": values,
        "morphology": fitted_morphology_name,
    }
