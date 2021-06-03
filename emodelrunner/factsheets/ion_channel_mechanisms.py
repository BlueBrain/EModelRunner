"""To extract ion channel mechanisms information from static parameter files."""

import logging
import re

from emodelrunner.load import load_emodel_params
from emodelrunner.json_utilities import load_package_json


logger = logging.getLogger(__name__)


def edit_dist_func(value):
    """Edit function expression to be latex and plot readable.

    Args:
        value (str): the distribution function expressed as a string.
            ex: "(-0.8696 + 2.087*math.exp((x)*0.0031))*3.1236056887012746e-06"

    Returns:
        latex (str): a latex-compatible version of the distrib. function
            ex: "(-0.8696 + 2.087*e^{x*0.0031})*3.1236056887012746e-06"
        value (str): a plottable version of the distrib. function
            ex: "(-0.8696 + 2.087exp(x*0.0031))*3.1236056887012746e-06"
    """
    if "math" in value:
        value = value.replace("math.", "")
    if "(x)" in value:
        value = value.replace("(x)", "x")
    latex = re.sub(r"exp*\(([0-9x*-.]*)\)", "e^{\\1}", value)
    return latex, value


def get_channel_and_equations(
    name, param_config, full_name, exp_fun, decay_fun, release_params
):
    """Returns the channel and a dictionary containing equation type (uniform or exp) and value.

    Args:
        name (str): the name of the ion channel and its parameter.
            should have the form parameter_channel (ex: "gCa_HVAbar_Ca_HVA2")
        param_config (dict): parameter dictionary taken from parameter data file.
            should have a "dist" key if the distribution is exponential.
        full_name (str): should have the form name.section
        exp_fun (str): the distribution function expressed as a string.
            ex: "(-0.8696 + 2.087*math.exp((x)*0.0031))*3.1236056887012746e-06"
        decay_fun (str): the decay function expressed as a string.
        release_params (dict): final parameters of the optimised cell.

    Returns:
        channel (str): name of the channel (ex: "Ca_HVA2")
        biophys (str): parameter name (ex: "gCa_HVAbar")
        equations (dict): dictionary containing equation values (for plotting and latex display)
            and type (uniform or exponential)
    """
    # parameter value (obtained from optimisation)
    value = release_params[full_name]

    decay_cst = None
    if decay_fun:
        decay_cst = release_params["constant.distribution_decay"]

    # isolate channel and biophys
    split_name = name.split("_")
    if len(split_name) == 4:
        biophys = "_".join(split_name[0:2])
        channel = "_".join(split_name[2:4])
    elif len(split_name) == 3:
        biophys = split_name[0]
        channel = "_".join(split_name[1:3])
    elif len(split_name) == 2:
        biophys = split_name[0]
        channel = split_name[1]

    # type
    if "dist" in param_config:
        if param_config["dist"] == "exp":
            type_ = "exponential"
            value = exp_fun.format(distance="x", value=value)
            latex, plot = edit_dist_func(value)
        elif param_config["dist"] == "decay":
            type_ = "decay"
            value = decay_fun.format(distance="x", value=value, constant=decay_cst)
            latex, plot = edit_dist_func(value)
        else:
            logger.warning(
                "dist is set to %s. Expected 'exp' or 'decay'. Set type to exponential anyway.",
                param_config["dist"],
            )
    else:
        type_ = "uniform"
        latex = value
        plot = value

    return channel, biophys, {"latex": latex, "plot": plot, "type": type_}


def append_equation(location_map, section, channel, biophys, equation_dict):
    """Append equation to location map dict."""
    # do not take into account "all" section
    # set default to create keys then add equations
    # this allows to either create channel data or append to channel key
    if section == "alldend":
        location_map["all dendrites"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["all dendrites"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "somadend":
        location_map["all dendrites"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["all dendrites"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
        location_map["somatic"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["somatic"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "somaxon":
        location_map["somatic"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["somatic"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
        location_map["axonal"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["axonal"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "allact":
        location_map["all dendrites"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["all dendrites"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
        location_map["somatic"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["somatic"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
        location_map["axonal"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["axonal"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "apical":
        location_map["apical"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["apical"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "basal":
        location_map["basal"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["basal"]["channels"][channel]["equations"][biophys] = equation_dict
    elif section == "axonal":
        location_map["axonal"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["axonal"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict
    elif section == "somatic":
        location_map["somatic"]["channels"].setdefault(
            channel, {"equations": {biophys: equation_dict}}
        )
        location_map["somatic"]["channels"][channel]["equations"][
            biophys
        ] = equation_dict


def clean_location_map(location_map):
    """Remove empty locations."""
    for key, loc in list(location_map.items()):
        if not loc["channels"]:
            location_map.pop(key)


def get_mechanisms_data(emodel, release_params_path, params_path):
    """Return a dictionary containing channel mechanisms for each section."""
    # pylint: disable=too-many-locals
    release_params = load_emodel_params(params_path=release_params_path, emodel=emodel)

    params = load_package_json(params_path)

    decay_func = None
    if "decay" in params["distributions"].keys():
        decay_func = params["distributions"]["decay"]["fun"]

    parameters = params["parameters"]
    exp_fun = params["distributions"]["exp"]["fun"]

    location_map = {
        "all dendrites": {"channels": {}},
        "apical": {"channels": {}},
        "basal": {"channels": {}},
        "somatic": {"channels": {}},
        "axonal": {"channels": {}},
    }

    for section, params in parameters.items():
        # do not take into account "comment"
        if isinstance(params, list):
            for param_config in params:
                name = param_config["name"]
                full_name = ".".join((name, section))

                # only take into account parameters present in finals.json
                if (
                    full_name in release_params
                    and full_name != "constant.distribution_decay"
                ):
                    channel, biophys, equation_dict = get_channel_and_equations(
                        name,
                        param_config,
                        full_name,
                        exp_fun,
                        decay_func,
                        release_params,
                    )

                    # append equation in location map
                    append_equation(
                        location_map, section, channel, biophys, equation_dict
                    )

    # remove empty locations
    clean_location_map(location_map)

    values = [
        {
            "tooltip": "",
            "location_map": location_map,
            "unit": "",
            "name": "list of ion channel mechanisms",
        }
    ]
    return {"name": "Channel mechanisms", "values": values}
