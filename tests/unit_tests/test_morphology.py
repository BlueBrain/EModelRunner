"""Unit tests for the morphology module."""

from pathlib import Path

from pytest import raises


from emodelrunner.load import load_config, get_morph_args
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

        sscx_morph = create_morphology(get_morph_args(config), PackageType.sscx)
        assert isinstance(sscx_morph, SSCXNrnFileMorphology)
        thal_morph = create_morphology(get_morph_args(config), PackageType.thalamus)
        assert isinstance(thal_morph, ThalamusNrnFileMorphology)

        with raises(ValueError):
            create_morphology(get_morph_args(config), "unknown_package_type")
