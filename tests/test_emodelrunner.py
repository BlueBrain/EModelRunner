"""Contains tests for the workflow."""
# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
# pylint: disable=import-error
import os
import numpy as np
import subprocess

from emodelrunner.create_hoc import get_hoc, write_hocs
from emodelrunner.json_utilities import load_package_json
from emodelrunner.load import (
    load_config,
    get_hoc_paths_args,
    load_emodel_params,
    find_param_file,
    load_amps,
)
from emodelrunner.factsheets.morphology_features import MorphologyFactsheetBuilder
from emodelrunner.factsheets.physiology_features import physiology_factsheet_info
from emodelrunner.factsheets.experimental_features import (
    get_exp_features_data,
    load_emodel_recipe_dict,
    get_morphology_prefix_from_recipe,
    load_raw_exp_features,
    load_feature_units,
    load_emodel_fitness,
)
from emodelrunner.write_factsheets import (
    get_morph_path,
    get_morph_name_dict,
    get_emodel,
    get_mechanisms_data,
    write_metype_json_from_config,
    write_emodel_json_from_config,
)
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


def test_metype_factsheet_exists():
    """Check that the me-type factsheet json file has been created."""
    configfile = "config_singlestep.ini"
    output_dir = "factsheets"

    with cwd(example_dir):
        config = load_config(filename=configfile)
        subprocess.call(["sh", "run_py.sh", configfile])
        write_metype_json_from_config(config, output_dir)
        write_emodel_json_from_config(config, output_dir)

    metype_factsheet = os.path.join(example_dir, "factsheets", "me_type_factsheet.json")
    emodel_factsheet = os.path.join(example_dir, "factsheets", "e_model_factsheet.json")

    assert os.path.isfile(metype_factsheet)
    assert os.path.isfile(emodel_factsheet)


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
    constants_path = os.path.join(
        config.get("Paths", "constants_dir"), config.get("Paths", "constants_file")
    )
    recipes_path = "/".join(
        (config.get("Paths", "recipes_dir"), config.get("Paths", "recipes_file"))
    )
    params_path = "/".join(
        (config.get("Paths", "params_dir"), config.get("Paths", "params_file"))
    )

    emodel = get_emodel(constants_path)
    recipe = load_emodel_recipe_dict(recipes_path, emodel)
    original_feat = load_raw_exp_features(recipe)
    units = load_feature_units()
    fitness = load_emodel_fitness(params_path, emodel)
    prefix = get_morphology_prefix_from_recipe(recipe)
    # tested func
    feat_dict = get_exp_features_data(emodel, recipes_path, params_path)

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
    _, morph_fname = get_morph_path(config)
    morph_name_dict = get_morph_name_dict(morph_fname)
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
    constants_path = os.path.join(
        config.get("Paths", "constants_dir"), config.get("Paths", "constants_file")
    )
    emodel = get_emodel(constants_path)
    recipes_path = "/".join(
        (config.get("Paths", "recipes_dir"), config.get("Paths", "recipes_file"))
    )
    params_filepath = find_param_file(recipes_path, emodel)
    params_path = "/".join(
        (config.get("Paths", "params_dir"), config.get("Paths", "params_file"))
    )

    release_params = load_emodel_params(params_path=params_path, emodel=emodel)

    definitions = load_package_json(params_filepath)

    parameters = definitions["parameters"]

    # output to check
    mech_dict = get_mechanisms_data(emodel, params_path, params_filepath)

    assert mech_dict["values"][0]["location_map"]
    for loc_name, loc in mech_dict["values"][0]["location_map"].items():
        assert loc["channels"]
        for channel_name, channel in loc["channels"].items():
            assert channel["equations"]
            for mech_name, mech in channel["equations"].items():
                mech_name_for_params = "_".join((mech_name, channel_name))
                new_loc_name, idx = get_loc_from_params(
                    loc_name, mech_name_for_params, parameters
                )
                mech_name_for_final_params = ".".join(
                    (mech_name_for_params, new_loc_name)
                )
                if mech["type"] == "exponential":
                    assert "dist" in parameters[new_loc_name][idx]
                    assert parameters[new_loc_name][idx]["dist"] == "exp"
                    assert (
                        str(release_params[mech_name_for_final_params]) in mech["plot"]
                    )
                    assert (
                        str(release_params[mech_name_for_final_params]) in mech["latex"]
                    )
                elif mech["type"] == "decay":
                    assert "dist" in parameters[new_loc_name][idx]
                    assert parameters[new_loc_name][idx]["dist"] == "decay"
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


def check_anatomy(config):
    """Checks that all anatomy data is positive and exists.

    Fields include axon and soma.
    Fields can either include basal and apical, or just dendrite.

    Checks that there is no empty list or dict.
    Checks that data exists and is a float/int and is positive.
    Checks that there is no anatomy field missing.
    """
    morph_dir, morph_fname = get_morph_path(config)

    morph_factsheet_builder = MorphologyFactsheetBuilder(
        os.path.join(morph_dir, morph_fname)
    )
    ana_dict = morph_factsheet_builder.get_all_feature_values()
    ana_dict = {"values": ana_dict, "name": "Anatomy"}
    left_to_check_1 = [
        "total axon length",
        "mean axon volume",
        "axon maximum branch order",
        "axon maximum section length",
        "total apical length",
        "mean apical volume",
        "apical maximum branch order",
        "apical maximum section length",
        "total basal length",
        "mean basal volume",
        "basal maximum branch order",
        "basal maximum section length",
        "soma diameter",
    ]
    left_to_check_2 = [
        "total axon length",
        "mean axon volume",
        "axon maximum branch order",
        "axon maximum section length",
        "total dendrite length",
        "mean dendrite volume",
        "dendrite maximum branch order",
        "dendrite maximum section length",
        "soma diameter",
    ]
    lists_to_check = [left_to_check_1, left_to_check_2]

    assert ana_dict["values"]
    for item in ana_dict["values"]:
        assert isinstance(item["value"], (float, int, np.floating, np.integer))
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
    # get current amplitude
    amps_path = os.path.join(
        config.get("Paths", "protocol_amplitudes_dir"),
        config.get("Paths", "protocol_amplitudes_file"),
    )
    step_number = config.getint("Protocol", "run_step_number")
    amps, _ = load_amps(amps_path)
    current_amplitude = amps[step_number - 1]

    # get parameters from config
    stim_start = config.getint("Protocol", "stimulus_delay")
    stim_duration = config.getint("Protocol", "stimulus_duration")

    # get data path from run.py output
    fname = "soma_voltage_step{}.dat".format(step_number)
    fpath = os.path.join("python_recordings", fname)
    data = np.loadtxt(fpath)

    phys_dict = physiology_factsheet_info(
        time=data[:, 0],
        voltage=data[:, 1],
        current_amplitude=current_amplitude,
        stim_start=stim_start,
        stim_duration=stim_duration,
    )
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
    with cwd(example_dir):
        config = load_config(filename="config_singlestep.ini")
        check_features(config)
        check_morph_name(config)
        check_mechanisms(config)
        check_physiology(config)
        check_anatomy(config)
