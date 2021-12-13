# Copyright (c) BBP/EPFL 2021.
# This work is licenced under Creative Common CC BY-NC-SA-4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)

./compile_mechanisms.sh

python -m emodelrunner.run --config_path $1
