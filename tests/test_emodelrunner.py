"""Contains tests for the workflow."""
# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=import-error
import configparser
from contextlib import contextmanager
import os
import numpy as np
import subprocess

from emodelrunner.create_hoc import get_hoc, write_hocs
from emodelrunner.load import load_config
from emodelrunner.write_factsheets import (
    get_morph_data,
    get_physiology_data,
    get_morph_name,
    get_emodel,
    get_recipe,
    get_prefix,
    get_exp_features_data,
    get_mechanisms_data,
    load_raw_exp_features,
    load_feature_units,
    load_fitness,
    get_param_data,
    write_metype_json,
    write_etype_json,
    write_morph_json,
)

from emodelrunner.run import main as run
from tests.sample_dir.old_run import main as old_run

data_dir = os.path.join("tests", "data")
example_dir = os.path.join("tests", "sample_dir")


@contextmanager
def cwd(path):
    """Cwd function that can be used in a context manager."""
    old_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old_dir)


def test_voltages():
    """Test to compare the voltages produced via python and hoc.

    The cells are run with subprocess, because if they are called directly from the module,
    neuron 'remembers' the cell template and that could make the other tests fail.
    """
    threshold = 1e-3
    threshold_py_recs = 1e-8

    # rewrite hocs and run cells
    run_hoc_filename = "run.hoc"

    with cwd(example_dir):
        # write hocs
        config = load_config(filename=None)
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(config=config, syn_temp_name="hoc_synapses")
        write_hocs(config, cell_hoc, simul_hoc, run_hoc, run_hoc_filename, syn_hoc)

        subprocess.call(["sh", "run_py.sh"])
        subprocess.call(["python", "old_run.py"])
        subprocess.call(["sh", "./run_hoc.sh"])

    for idx in range(3):
        hoc_path = os.path.join(
            example_dir, "hoc_recordings", "soma_voltage_step%d.dat" % (idx + 1)
        )
        py_path = os.path.join(
            example_dir, "python_recordings", "soma_voltage_step%d.dat" % (idx + 1)
        )
        old_py_path = os.path.join(
            example_dir, "old_python_recordings", "soma_voltage_step%d.dat" % (idx + 1)
        )

        hoc_voltage = np.loadtxt(hoc_path)
        py_voltage = np.loadtxt(py_path)
        old_py_voltage = np.loadtxt(old_py_path)

        rms = np.sqrt(np.mean((hoc_voltage[:, 1] - py_voltage[:, 1]) ** 2))
        rms_py_recs = np.sqrt(np.mean((old_py_voltage[:, 1] - py_voltage[:, 1]) ** 2))
        assert rms < threshold
        assert rms_py_recs < threshold_py_recs


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
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(config=config, syn_temp_name="hoc_synapses")
        write_hocs(config, cell_hoc, simul_hoc, run_hoc, run_hoc_filename, syn_hoc)

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
    threshold = 0.1
    threshold_py_recs = 0.1

    # rewrite hocs and run cells
    run_hoc_filename = "run.hoc"

    # start with hoc, to compile mechs
    with cwd(example_dir):
        # write hocs
        config = load_config(filename=configfile)
        cell_hoc, syn_hoc, simul_hoc, run_hoc = get_hoc(config=config, syn_temp_name="hoc_synapses")
        write_hocs(config, cell_hoc, simul_hoc, run_hoc, run_hoc_filename, syn_hoc)

        subprocess.call(["sh", "./run_hoc.sh"])
        subprocess.call(["sh", "run_py.sh", configfile])
        subprocess.call(["python", "old_run.py", "--c", configfile])

    # load output
    hoc_path = os.path.join(example_dir, "hoc_recordings", "soma_voltage_vecstim.dat")
    py_path = os.path.join(example_dir, "python_recordings", "soma_voltage_vecstim.dat")
    old_py_path = os.path.join(example_dir, "old_python_recordings", "soma_voltage_vecstim.dat")

    hoc_voltage = np.loadtxt(hoc_path)
    py_voltage = np.loadtxt(py_path)
    old_py_voltage = np.loadtxt(old_py_path)

    # check rms
    rms = np.sqrt(np.mean((hoc_voltage[:, 1] - py_voltage[:, 1]) ** 2))
    rms_py_recs = np.sqrt(np.mean((old_py_voltage[:, 1] - py_voltage[:, 1]) ** 2))
    assert rms < threshold
    assert rms_py_recs < threshold_py_recs


def test_metype_factsheet_exists():
    """Check that the me-type factsheet json file has been created."""

    config = load_config(filename=None)

    output_dir = "factsheets"
    with cwd(example_dir):
        write_metype_json(config, output_dir)
        write_etype_json(config, output_dir)
        write_morph_json(config, output_dir)

    metype_factsheet = os.path.join(example_dir, "factsheets", "me_type_factsheeet.json")
    etype_factsheet = os.path.join(example_dir, "factsheets", "e_type_factsheeet.json")
    mtype_factsheet = os.path.join(example_dir, "factsheets", "morphology_factsheeet.json")
    assert os.path.isfile(metype_factsheet)
    assert os.path.isfile(etype_factsheet)
    assert os.path.isfile(mtype_factsheet)


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
    emodel = get_emodel(config)
    recipe = get_recipe(config, emodel)
    original_feat = load_raw_exp_features(recipe)
    units = load_feature_units()
    fitness = load_fitness(config, emodel)
    prefix = get_prefix(config, recipe)
    # tested func
    feat_dict = get_exp_features_data(config)

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
                    assert feat["unit"] == units[feat["name"]]
                    assert feat["model fitness"] == fitness[key_fitness]


def check_morph_name(config):
    """Checks that factsheet morph name corresponds to package morph file."""
    morph_name_dict = get_morph_name(config)
    assert os.path.isfile(os.path.join("morphology", morph_name_dict["value"] + ".asc"))


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
    release_params, parameters, _, _ = get_param_data(config)
    # output to check
    mech_dict = get_mechanisms_data(config)

    assert mech_dict["values"][0]["location_map"]
    for loc_name, loc in mech_dict["values"][0]["location_map"].items():
        assert loc["channels"]
        for channel_name, channel in loc["channels"].items():
            assert channel["equations"]
            for mech_name, mech in channel["equations"].items():
                mech_name_for_params = "_".join((mech_name, channel_name))
                new_loc_name, idx = get_loc_from_params(loc_name, mech_name_for_params, parameters)
                mech_name_for_final_params = ".".join((mech_name_for_params, new_loc_name))
                if mech["type"] == "exponential":
                    assert "dist" in parameters[new_loc_name][idx]
                    assert parameters[new_loc_name][idx]["dist"] == "exp"
                    assert str(release_params[mech_name_for_final_params]) in mech["plot"]
                    assert str(release_params[mech_name_for_final_params]) in mech["latex"]
                elif mech["type"] == "decay":
                    assert "dist" in parameters[new_loc_name][idx]
                    assert parameters[new_loc_name][idx]["dist"] == "decay"
                    assert str(release_params[mech_name_for_final_params]) in mech["plot"]
                    assert str(release_params[mech_name_for_final_params]) in mech["latex"]
                    assert str(release_params["constant.distribution_decay"]) in mech["plot"]
                    assert str(release_params["constant.distribution_decay"]) in mech["latex"]
                else:
                    assert mech["type"] == "uniform"
                    assert release_params[mech_name_for_final_params] == mech["latex"]
                    assert release_params[mech_name_for_final_params] == mech["plot"]


def check_anatomy(config):
    """Checks that all anatomy data is positive and exists.

    Fields include axon and soma.
    Fields can either include basal and apical, or just dendrite.

    Checks that there is no empty list or dict.
    Checks that data exists and is a float/int and is positive.
    Checks that there is no anatomy field missing.
    """
    ana_dict = get_morph_data(config)
    left_to_check_1 = [
        "total axon length",
        "total axon volume",
        "axon maximum branch order",
        "axon maximum section length",
        "total apical length",
        "total apical volume",
        "apical maximum branch order",
        "apical maximum section length",
        "total basal length",
        "total basal volume",
        "basal maximum branch order",
        "basal maximum section length",
        "soma diameter",
    ]
    left_to_check_2 = [
        "total axon length",
        "total axon volume",
        "axon maximum branch order",
        "axon maximum section length",
        "total dendrite length",
        "total dendrite volume",
        "dendrite maximum branch order",
        "dendrite maximum section length",
        "soma diameter",
    ]
    lists_to_check = [left_to_check_1, left_to_check_2]

    assert ana_dict["values"]
    for item in ana_dict["values"]:
        assert isinstance(item["value"], (float, int, np.integer))
        assert item["value"] > 0

        for l in lists_to_check:
            if item["name"] in l:
                l.remove(item["name"])

    assert len(lists_to_check[0]) == 0 or len(lists_to_check[1]) == 0


def check_physiology(config):
    """Checks that all physiology values exist.

    Checks that there is no empty list or dict.
    Checks that data exists and is a float and is positive (except for membrane pot.).
    Checks that there is no physiology field missing.
    """
    phys_dict = get_physiology_data(config)
    left_to_check = [
        "input resistance",
        "membrane time constant",
        "resting membrane potential",
    ]

    assert phys_dict["values"]
    for item in phys_dict["values"]:
        assert isinstance(item["value"], float)
        if item["name"] in ["input resistance", "membrane time constant"]:
            assert item["value"] >= 0
        left_to_check.remove(item["name"])

    assert len(left_to_check) == 0


def test_factsheets_fcts():
    """Test dictionary output from functions used for factsheets."""
    config = load_config()

    with cwd(example_dir):
        check_features(config)
        check_morph_name(config)
        check_mechanisms(config)
        check_physiology(config)
        check_anatomy(config)
