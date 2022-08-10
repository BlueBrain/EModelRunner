"""Unit tests for the factsheets output."""

# Copyright 2020-2022 Blue Brain Project / EPFL

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
import json

import numpy as np
import pytest

from emodelrunner.load import load_config
from emodelrunner.run import main as run_emodel
from emodelrunner.factsheets import morphology_features
from emodelrunner.factsheets.output import (
    get_stim_params_from_config_for_physiology_factsheet,
    write_metype_json_from_config,
    write_emodel_json,
)
from emodelrunner.factsheets.experimental_features import (
    get_exp_features_data,
)
from emodelrunner.factsheets.ion_channel_mechanisms import get_mechanisms_data
from emodelrunner.factsheets.physiology_features import physiology_factsheet_info
from tests.utils import cwd


example_dir = Path(".") / "examples" / "sscx_sample_dir"


class TestMETypeFactsheet:
    """Test the metype factsheet."""

    @classmethod
    def setup_class(cls):
        """setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        protocol_key = "RmpRiTau"
        config_path_in_memodel_dir = Path("config") / "config_factsheets.ini"
        output_path = Path("factsheets") / "me_type_factsheet.json"

        with cwd(example_dir):
            config = load_config(config_path=config_path_in_memodel_dir)
            run_emodel(config_path=config_path_in_memodel_dir)

        voltage_path = Path("python_recordings") / ("_." + protocol_key + ".soma.v.dat")
        morphology_path = (
            Path("morphology")
            / "dend-C231296A-P4B2_axon-C200897C-P2_-_Scale_x1.000_y0.975_z1.000.asc"
        )
        assert (Path(example_dir) / morphology_path).is_file()

        # need to move to example_dir to be able to open protocol file
        with cwd(example_dir):
            write_metype_json_from_config(
                config,
                voltage_path,
                morphology_path,
                output_path,
                protocol_key=protocol_key,
            )

        cls.output_path = Path(example_dir) / output_path

    @pytest.mark.xdist_group(name="TestMETypeFactsheet")
    def test_metype_factsheet_exists(self):
        """Test if the factsheet file is created."""
        assert self.output_path.is_file()

    @pytest.mark.xdist_group(name="TestMETypeFactsheet")
    def test_physiology_features(self):
        """Checks that all physiology values exist.

        Checks that there is no empty list or dict.
        Checks that data exists and is a float and is positive (except for membrane pot.).
        Checks that there is no physiology field missing.
        """
        protocol_key = "RmpRiTau"
        # get stimulus amp, delay and duration
        prot_path = Path(example_dir) / "config" / "protocols" / "RmpRiTau.json"

        stim_params = get_stim_params_from_config_for_physiology_factsheet(
            prot_path, protocol_key
        )
        current_amplitude, stim_start, stim_duration = stim_params

        # get data path from run.py output
        voltage_path = (
            Path(example_dir)
            / "python_recordings"
            / ("_." + protocol_key + ".soma.v.dat")
        )
        data = np.loadtxt(voltage_path)

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


def test_emodel_factsheet_exists():
    """Tests if the emodel factsheet output file is created."""

    output_path = example_dir / "factsheets" / "e_model_factsheet.json"
    emodel = "cADpyr_L4UPC"
    mtype = "_"

    unoptimized_params_path = Path(example_dir) / "config" / "params" / "pyr.json"
    with open(unoptimized_params_path) as json_file:
        unoptimized_params_dict = json.load(json_file)

    optimized_params_path = Path(example_dir) / "config" / "params" / "final.json"
    with open(optimized_params_path) as json_file:
        optimized_params_dict = json.load(json_file)

    features_path = Path(example_dir) / "config" / "features" / "cADpyr_L4PC.json"
    with open(features_path) as json_file:
        features_dict = json.load(json_file)

    feature_units_path = Path(example_dir) / "config" / "features" / "units.json"
    with open(feature_units_path) as json_file:
        feature_units_dict = json.load(json_file)

    write_emodel_json(
        emodel,
        mtype,
        features_dict,
        feature_units_dict,
        unoptimized_params_dict,
        optimized_params_dict,
        output_path,
    )

    assert output_path.is_file()


def test_anatomy_features():
    """Checks that all anatomy data is positive and exists.

    Fields include axon and soma.
    Fields can either include basal and apical, or just dendrite.

    Checks that there is no empty list or dict.
    Checks that data exists and is a float/int and is positive.
    Checks that there is no anatomy field missing.
    """
    morphology_path = (
        Path(example_dir)
        / "morphology"
        / "dend-C231296A-P4B2_axon-C200897C-P2_-_Scale_x1.000_y0.975_z1.000.asc"
    )

    morph_factsheet_builder = morphology_features.SSCXMorphologyFactsheetBuilder(
        morphology_path
    )

    ana_dict = morph_factsheet_builder.get_feature_values()
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


def test_mechanisms():
    """Checks factsheet mechanisms.

    Checks that there is no empty list or dict.
    Checks that 'type' is either exponential or decay or uniform.
    Checks that if type is exponential,
        there is an according ['dist']='exp' field in parameter file.
    Idem if type is decay
    Checks that all values are identical to files.
    """

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

    # original data
    emodel = "cADpyr_L4UPC"
    optimized_params_path = example_dir / "config" / "params" / "final.json"
    with open(optimized_params_path) as json_file:
        optimized_params_dict = json.load(json_file)

    release_params = optimized_params_dict[emodel]["params"]

    unoptimized_params_path = example_dir / "config" / "params" / "pyr.json"
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


def test_experimental_feature_values():
    """Checks factsheet features.

    Checks that there is no empty list or dictionary.
    Checks that features name, mean, and std are identical to the ones in feature file.
    Checks that units correspond to the ones in unit file.
    Checks that model fitnesses correspond to the ones in fitness file."""

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

    # original files data
    optimized_params_path = example_dir / "config" / "params" / "final.json"
    with open(optimized_params_path) as json_file:
        optimized_params_dict = json.load(json_file)

    emodel = "cADpyr_L4UPC"
    features_path = example_dir / "config" / "features" / "cADpyr_L4PC.json"
    with open(features_path) as json_file:
        original_feat = json.load(json_file)

    feature_units_path = example_dir / "config" / "features" / "units.json"
    with open(feature_units_path) as json_file:
        feature_units_dict = json.load(json_file)
    fitness = optimized_params_dict[emodel]["fitness"]
    morph_prefix = "_"

    # tested func
    feat_dict = get_exp_features_data(
        emodel, morph_prefix, original_feat, feature_units_dict, optimized_params_dict
    )

    for items in feat_dict["values"]:
        assert items.items()
        for stim_name, stim_data in items.items():
            assert stim_data.items()
            for loc_name, loc_data in stim_data.items():
                assert loc_data
                for feat in loc_data["features"]:
                    original = original_feat[stim_name][loc_name]
                    key_fitness = ".".join(
                        (morph_prefix, stim_name, loc_name, feat["name"])
                    )

                    assert check_feature_mean_std(original, feat)
                    assert feat["unit"] == feature_units_dict[feat["name"]]
                    assert feat["model fitness"] == fitness[key_fitness]


def test_get_stim_params_for_physiology():
    """Test get_stim_params_function."""
    # test function's output
    prot_path = Path(example_dir) / "config" / "protocols" / "RmpRiTau.json"

    stim_params = get_stim_params_from_config_for_physiology_factsheet(
        prot_path, "RmpRiTau"
    )
    current_amplitude, stim_start, stim_duration = stim_params

    assert current_amplitude == -0.01
    assert stim_start == 1000.0
    assert stim_duration == 1000.0

    # test function's exception
    prot_path = example_dir / "config" / "protocols" / "multiprotocols.json"

    with pytest.raises(Exception):
        stim_params = get_stim_params_from_config_for_physiology_factsheet(
            prot_path, "MultiStepProtocolNoHolding"
        )
