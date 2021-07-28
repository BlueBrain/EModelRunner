"""Contains tests for the workflow."""
# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=import-error
import os
from pathlib import Path
import json
import numpy as np
import subprocess

from emodelrunner.create_hoc import get_hoc, write_hocs
from emodelrunner.load import (
    load_config,
    get_hoc_paths_args,
)
from emodelrunner.factsheets.experimental_features import (
    get_exp_features_data,
    get_morphology_prefix_from_recipe,
)
from emodelrunner.factsheets.ion_channel_mechanisms import get_mechanisms_data
from tests.utils import cwd

data_dir = os.path.join("tests", "data")
example_dir = os.path.join("examples", "sscx_sample_dir")


def test_voltages():
    """Test to compare the voltages produced via python and hoc.

    The cells are run with subprocess, because if they are called directly from the module,
    neuron 'remembers' the cell template and that could make the other tests fail.
    """
    threshold = 1e-5

    # rewrite hocs and run cells
    run_hoc_filename = "run.hoc"
    configfile = "config_allsteps.ini"

    with cwd(example_dir):
        # write hocs
        config = load_config(filename=configfile)
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(
            config=config, syn_temp_name="hoc_synapses"
        )
        hoc_paths = get_hoc_paths_args(config)
        write_hocs(hoc_paths, cell_hoc, simul_hoc, run_hoc, run_hoc_filename, syn_hoc)

        subprocess.call(["sh", "run_py.sh", configfile])
        subprocess.call(["sh", "./run_hoc.sh"])

    for idx in range(3):
        hoc_path = os.path.join(
            example_dir, "hoc_recordings", "soma_voltage_step%d.dat" % (idx + 1)
        )
        py_path = os.path.join(
            example_dir, "python_recordings", "soma_voltage_step%d.dat" % (idx + 1)
        )

        hoc_voltage = np.loadtxt(hoc_path)
        py_voltage = np.loadtxt(py_path)

        rms = np.sqrt(np.mean((hoc_voltage[:, 1] - py_voltage[:, 1]) ** 2))
        assert rms < threshold


def test_synapses(configfile="config_synapses.ini"):
    """Test to compare the output of cell with synapses between our run.py and bglibpy.

    Attributes:
        configfile: the configuration file of the emodel.
    """

    threshold = 0.05

    # load bglibpy data
    bg_v = np.loadtxt(os.path.join(data_dir, "bglibpy_voltage.dat"))

    # rewrite hocs and run cell
    run_hoc_filename = "run.hoc"

    with cwd(example_dir):
        # write hocs
        config = load_config(filename=configfile)
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(
            config=config, syn_temp_name="hoc_synapses"
        )
        hoc_paths = get_hoc_paths_args(config)
        write_hocs(hoc_paths, cell_hoc, simul_hoc, run_hoc, run_hoc_filename, syn_hoc)

        subprocess.call(["sh", "run_py.sh", configfile])

    py_path = os.path.join(example_dir, "python_recordings", "soma_voltage_vecstim.dat")
    py_v = np.loadtxt(py_path)

    # compare
    rms = np.sqrt(np.mean((bg_v - py_v[:, 1]) ** 2))
    assert rms < threshold


def test_synapses_hoc_vs_py_script(configfile="config_synapses.ini"):
    """Test to compare the voltages produced via python and hoc.

    Attributes:
        configfile : name of config file in /config to use when running script / creating hoc
    """
    threshold = 1e-5

    # rewrite hocs and run cells
    run_hoc_filename = "run.hoc"

    # start with hoc, to compile mechs
    with cwd(example_dir):
        # write hocs
        config = load_config(filename=configfile)
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(
            config=config, syn_temp_name="hoc_synapses"
        )
        hoc_paths = get_hoc_paths_args(config)
        write_hocs(hoc_paths, cell_hoc, simul_hoc, run_hoc, run_hoc_filename, syn_hoc)

        subprocess.call(["sh", "./run_hoc.sh"])
        subprocess.call(["sh", "run_py.sh", configfile])

    # load output
    hoc_path = os.path.join(example_dir, "hoc_recordings", "soma_voltage_vecstim.dat")
    py_path = os.path.join(example_dir, "python_recordings", "soma_voltage_vecstim.dat")

    hoc_voltage = np.loadtxt(hoc_path)
    py_voltage = np.loadtxt(py_path)

    # check rms
    rms = np.sqrt(np.mean((hoc_voltage[:, 1] - py_voltage[:, 1]) ** 2))
    assert rms < threshold


def check_feature_mean_std(source, feat):
    """Checks that feature mean and std are equal to the original ones.

    Args:
        source (list): list of dict containing original features.
        feat (dict): feature to be checked.

    Returns True if mean and std were found in source and were equal to tested ones.
    """
    for item in source:
        if item["feature"] == feat["name"]:
            assert feat["values"][0]["mean"] == item["val"][0]
            assert feat["values"][0]["std"] == item["val"][1]
            return True
    return False


def check_features(config):
    """Checks factsheet features.

    Checks that there is no empty list or dictionary.
    Checks that features name, mean, and std are identical to the ones in feature file.
    Checks that units correspond to the ones in unit file.
    Checks that model fitnesses correspond to the ones in fitness file."""
    # original files data
    recipes_path = Path(".") / "emodel_parameters" / "recipe.json"

    with open(recipes_path) as json_file:
        recipes_dict = json.load(json_file)

    optimized_params_path = Path(".") / "emodel_parameters" / "params" / "final.json"
    with open(optimized_params_path) as json_file:
        optimized_params_dict = json.load(json_file)

    emodel = config.get("Cell", "emodel")
    features_path = Path(".") / "emodel_parameters" / "features" / "cADpyr_L5PC.json"
    with open(features_path) as json_file:
        original_feat = json.load(json_file)

    feature_units_path = Path("emodel_parameters") / "features" / "units.json"
    with open(feature_units_path) as json_file:
        feature_units_dict = json.load(json_file)
    fitness = optimized_params_dict[emodel]["fitness"]
    prefix = get_morphology_prefix_from_recipe(emodel=emodel, recipe=recipes_dict)

    # tested func
    feat_dict = get_exp_features_data(
        emodel, recipes_dict, original_feat, feature_units_dict, optimized_params_dict
    )

    for items in feat_dict["values"]:
        assert items.items()
        for stim_name, stim_data in items.items():
            assert stim_data.items()
            for loc_name, loc_data in stim_data.items():
                assert loc_data
                for feat in loc_data["features"]:
                    original = original_feat[stim_name][loc_name]
                    key_fitness = ".".join((prefix, stim_name, loc_name, feat["name"]))

                    assert check_feature_mean_std(original, feat)
                    assert feat["unit"] == feature_units_dict[feat["name"]]
                    assert feat["model fitness"] == fitness[key_fitness]


def get_locs_list(loc_name):
    """Return possible location list from a location name."""
    if loc_name == "all dendrites":
        return ["somadend", "alldend", "allact"]
    elif loc_name == "somatic":
        return ["somadend", "somatic", "allact", "somaxon"]
    elif loc_name == "axonal":
        return ["axonal", "allact", "somaxon"]
    elif loc_name == "apical":
        return ["apical", "allact"]
    elif loc_name == "basal":
        return ["basal", "allact"]
    return None


def get_loc_from_params(loc_name, mech_name_for_params, params):
    """Returns general location name and index of mechanism in the param dict.

    Args:
        loc_name (str): location name (dendrite, somatic, axonal)
        mech_name_for_params (str): mechanism name with the form mech_channel
            ex: "gCa_HVAbar_Ca_HVA2"
        params (dict): dictionary in which the mech is searched

    Returns:
        new_loc_name (str): general location name under which the channel can be found
            (somadend, alldend, somatic, axonal, allact, somaxon, apical, basal)
        idx (int): index of the channel in the list under location key
    """
    locs = get_locs_list(loc_name)

    for loc in locs:
        if loc in params.keys():
            for i, param in enumerate(params[loc]):
                if param["name"] == mech_name_for_params:
                    return loc, i

    return "", 0


def check_mechanisms(config):
    """Checks factsheet mechanisms.

    Checks that there is no empty list or dict.
    Checks that 'type' is either exponential or decay or uniform.
    Checks that if type is exponential,
        there is an according ['dist']='exp' field in parameter file.
    Idem if type is decay
    Checks that all values are identical to files.
    """
    # original data
    emodel = config.get("Cell", "emodel")
    optimized_params_path = Path(".") / "emodel_parameters" / "params" / "final.json"
    with open(optimized_params_path) as json_file:
        optimized_params_dict = json.load(json_file)

    release_params = optimized_params_dict[emodel]["params"]

    unoptimized_params_path = Path(".") / "emodel_parameters" / "params" / "pyr.json"
    with open(unoptimized_params_path) as json_file:
        unoptimized_params_dict = json.load(json_file)

    unoptimized_params = unoptimized_params_dict["parameters"]
    # output to check
    mech_dict = get_mechanisms_data(
        emodel, optimized_params_dict, unoptimized_params_dict
    )

    assert mech_dict["values"][0]["location_map"]
    for loc_name, loc in mech_dict["values"][0]["location_map"].items():
        assert loc["channels"]
        for channel_name, channel in loc["channels"].items():
            assert channel["equations"]
            for mech_name, mech in channel["equations"].items():
                mech_name_for_params = "_".join((mech_name, channel_name))
                new_loc_name, idx = get_loc_from_params(
                    loc_name, mech_name_for_params, unoptimized_params
                )
                mech_name_for_final_params = ".".join(
                    (mech_name_for_params, new_loc_name)
                )
                if mech["type"] == "exponential":
                    assert "dist" in unoptimized_params[new_loc_name][idx]
                    assert unoptimized_params[new_loc_name][idx]["dist"] == "exp"
                    assert (
                        str(release_params[mech_name_for_final_params]) in mech["plot"]
                    )
                    assert (
                        str(release_params[mech_name_for_final_params]) in mech["latex"]
                    )
                elif mech["type"] == "decay":
                    assert "dist" in unoptimized_params[new_loc_name][idx]
                    assert unoptimized_params[new_loc_name][idx]["dist"] == "decay"
                    assert (
                        str(release_params[mech_name_for_final_params]) in mech["plot"]
                    )
                    assert (
                        str(release_params[mech_name_for_final_params]) in mech["latex"]
                    )
                    assert (
                        str(release_params["constant.distribution_decay"])
                        in mech["plot"]
                    )
                    assert (
                        str(release_params["constant.distribution_decay"])
                        in mech["latex"]
                    )
                else:
                    assert mech["type"] == "uniform"
                    assert release_params[mech_name_for_final_params] == mech["latex"]
                    assert release_params[mech_name_for_final_params] == mech["plot"]


def test_factsheets_fcts():
    """Test dictionary output from functions used for factsheets."""
    with cwd(example_dir):
        config = load_config(filename="config_singlestep.ini")
        check_features(config)
        check_mechanisms(config)
