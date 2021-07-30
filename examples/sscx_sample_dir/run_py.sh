# Copyright (c) BBP/EPFL 2018; All rights reserved.                         
# Do not distribute without further notice.   

# preloaded=False not implemented yet in BluePyOpt mechanisms
if [ ! -f "x86_64/special" ]; then
    nrnivmodl mechanisms
fi

if [ $# -eq 0 ]
then
    python -m emodelrunner.run
else
    python -m emodelrunner.run --config_path $1
fi
