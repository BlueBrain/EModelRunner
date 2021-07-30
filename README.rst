############
EModelRunner
############

Runs cells from Blue Brain Project cell packages, such as sscx, synapse plasticity, etc.


Installing EModelRunner
=======================

The usual way to install EModelRunner is using pip.

In that case, you probably want to use a python 
`virtual environment <https://bbpteam.epfl.ch/project/spaces/display/BBPWFA/virtualenv>`_.

Pip install emodelrunner from the BBP Devpi server::

    pip install -i 'https://bbpteam.epfl.ch/repository/devpi/bbprelman/dev/+simple/' emodelrunner[bbp]

Hopefully this installation went smoothly. If it didn't, please create a Jira 
ticket, assign it to Aurelien Jaquier or Anil Tuncel, and explain as detailed as possible the problems you encountered.


Installing from source 
----------------------

If you want to make changes to emodelrunner, you might want to install it using the 
source repository. The same remarks of the section above apply, 
the only difference is that you clone the git repo::

   git clone ssh://bbpcode.epfl.ch/cells/emodelrunner.git

and run pip from inside the newly created emodelrunner subdirectory 
(don't forget the dot at the end of the command)::

    pip install -i https://bbpteam.epfl.ch/repository/devpi/bbprelman/dev/+simple --upgrade .[bbp]

Supported systems
-----------------

The code of emodelrunner can be installed on any POSIX system that supports 
pip-installable python code.


Dependencies
============

The main dependencies of EModelRunner are::

    Python3.6+ 
    Matplotlib
    Numpy
    Neurom
    H5py
    NEURON
    BluePyOpt

Ideally, follow the installation instructions of these tools, or use 
pre-installed versions.

Python
------

Modern Linux systems will have Python 2.7 or 3 installed.

Make sure you're using a recent version of pip. It's best to run ::

    pip install pip --upgrade

before installing anything else using pip.


Examples
========

Two examples are available under the example folder of this package: 

sscx_sample_dir, containing a cell with configurations for 3 simple step protocols and one synapse exciting protocol.

synplas_sample_dir, containing a cell with a protocol exposing the synapse plasticity phenomenon.

In both cases, running the cells can be done in three steps:

First, go to the folder you are interested in:

For the simple protocol cell:

    cd examples/sscx_sample_dir

For the synapse plasticity cell:

    cd examples/synplas_sample_dir

Then, compile the mechanisms using neuron:

    nrnivmodl mechanisms

Finally, running the cell with the appropriate script:
For the simple cell:

    sh run_py.sh

For the synapse plasticity cell:

    sh run.sh

The output can be found under python_recordings for the sscx cell, and under output.h5 for the synapse plasticity cell.

GUI
---

There is also a GUI available for the sscx cells. To launch it, you have to follow the first two steps of the previous example, and then type:

    python -m emodelrunner.GUI

The usage of the GUI is pretty much self-explanatory.

In the upper part of the left column, you have the display configuration. You may want to change the figure size depending on your screen size for optimal display.
In the lower part of the left column is the step and holding stimuli configuration. You can put both to custom stimulus and set them to 0 if you don't want to have any step stimulus.

In the right column you have the synapse stimuli configuration. Check the box of each synapse mtype you want to receive stimuli from.
The activated synapses will display on the right figure with red dots for excitatory synapses and yellow dots for inhibitory synapses.
You can then set on the right column at which time each synapse group should start firing, at which interval and how many times they should fire, and if they should have any noise.

In the center part of the GUI, you have two plots of the cell, the one on the left showing the voltage at each section, and the one on the right showing the synapses locations.
You can change the rotation of both plots in 3D with your mouse.
Below is a plot showing the voltage in the soma depending on time. On top, you have three buttons to (re)start the simulation, pause it or resume it.
