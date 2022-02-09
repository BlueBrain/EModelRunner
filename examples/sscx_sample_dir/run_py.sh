# Copyright (c) BBP/EPFL 2020-2022.
# This work is licenced under Creative Common CC BY-NC-SA-4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)

# preloaded=False not implemented yet in BluePyOpt mechanisms
if [ ! -f "x86_64/special" ]; then
    nrnivmodl mechanisms
fi

python -m emodelrunner.run --config_path $1
