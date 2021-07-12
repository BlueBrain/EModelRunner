if [ ! -f "x86_64/special" ]; then
    nrnivmodl mechanisms
fi
nrniv run.hoc
