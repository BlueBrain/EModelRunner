"""Configuration parsing."""

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


from configparser import ConfigParser
from enum import Enum


class PackageType(Enum):
    """Enumerator for the emodel package types."""

    sscx = "sscx"
    thalamus = "thalamus"
    synplas = "synplas"


class EModelConfigParser(ConfigParser):
    """Built-in ConfigParser annotated with package type."""

    def __init__(self):
        """Constructor."""
        super().__init__()

    @property
    def package_type(self):
        """Package type as a property."""
        return PackageType[self.get("Package", "type")]
