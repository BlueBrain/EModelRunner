"""GUI."""

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

import logging

from emodelrunner.GUI_utils.interface import GUI
from emodelrunner.parsing_utilities import get_parser_args, set_verbosity

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    args = get_parser_args()
    set_verbosity(args.verbosity)

    gui = GUI(config_path=args.config_path)
    gui.root.mainloop()
