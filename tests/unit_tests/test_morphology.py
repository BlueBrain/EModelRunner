"""Unit tests for the morphology module."""

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

from pytest import raises


from emodelrunner.load import load_config
from emodelrunner.morphology import (
    create_morphology,
    SSCXNrnFileMorphology,
    ThalamusNrnFileMorphology,
)
from emodelrunner.configuration import PackageType
from tests.utils import cwd

sscx_conf = Path("examples") / "sscx_sample_dir" / "config" / "config_allsteps.ini"


def test_create_morphology():
    """Unit test for create_morphology function."""

    sscx_dir = Path("examples") / "sscx_sample_dir"
    with cwd(sscx_dir):
        config = load_config(config_path=Path("config") / "config_allsteps.ini")

        sscx_morph = create_morphology(config.morph_args(), PackageType.sscx)
        assert isinstance(sscx_morph, SSCXNrnFileMorphology)
        thal_morph = create_morphology(config.morph_args(), PackageType.thalamus)
        assert isinstance(thal_morph, ThalamusNrnFileMorphology)

        with raises(ValueError):
            create_morphology(config.morph_args(), "unknown_package_type")
