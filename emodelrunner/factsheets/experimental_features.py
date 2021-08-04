"""Functionality to fetch the experimental features and parameters from the json files."""

import logging

logger = logging.getLogger(__name__)


def morphology_used_in_fitting(optimized_params_dict, emodel):
    """Returns the morphology name from finals.json used in model fitting."""
    emodel_params = optimized_params_dict[emodel]
    morph_path = emodel_params["morph_path"]
    morph_name = morph_path.split("/")[-1]
    return morph_name


def get_morphology_prefix_from_recipe(emodel, recipe):
    """Get the morphology prefix from an emodel recipe (e.g. '_' or 'L5TPCa')."""
    return recipe[emodel]["morphology"][0][0]


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


def get_exp_features_data(
    emodel, recipe_dict, features_dict, units, optimized_params_dict
):
    """Returns a dict containing mean and std of experimental features and model fitness."""
    # pylint: disable=too-many-locals
    # it is hard to reduce number of locals without reducing readibility
    fitness = optimized_params_dict[emodel]["fitness"]

    morphology_prefix = get_morphology_prefix_from_recipe(emodel, recipe_dict)

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
