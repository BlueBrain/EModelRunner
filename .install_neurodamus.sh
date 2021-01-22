#!/bin/sh

set -e

INSTALL_DIR=$1

if [ ! -e ${INSTALL_DIR}/.install_finished ]
then
    echo 'Neurodamus was not fully installed in previous build, installing ...'
    mkdir -p ${INSTALL_DIR}
    cd ${INSTALL_DIR}

    echo "Downloading neurodamus core ..." 
    rm -rf neurodamus-core
    git clone -q --depth 1 ssh://bbpcode.epfl.ch/sim/neurodamus-core
    
    echo "Downloading neocortex channels ..."
    rm -rf neocortex
    git clone -q --depth 1 --recursive ssh://bbpcode.epfl.ch/sim/models/neocortex

    echo "Downloading thalamus channels ..."
    rm -rf thalamus
    git clone -q --depth 1 --recursive ssh://bbpcode.epfl.ch/sim/models/thalamus

    # Remove this line once we have a canonical v6 sim
    cp neocortex/mod/v5/Ca_HVA.mod neocortex/mod/v6
    
    touch -f .install_finished
    echo "Neurodamus successfully installed"
else
    echo 'Neurodamus was successfully installed in previous build, not rebuilding'
fi
