# Copyright (c) BBP/EPFL 2018; All rights reserved.                         
# Do not distribute without further notice.   

if [ ! -f "x86_64/special" ]; then
    nrnivmodl mechanisms
fi

python -m emodelrunner.run_pairsim --config_path "config/config_pairsim.ini"
