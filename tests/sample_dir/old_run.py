"""Python script to run cell model.

@remarks Copyright (c) BBP/EPFL 2018; All rights reserved.
         Do not distribute without further notice.

"""

from __future__ import print_function


# pylint: disable=C0325, W0212, F0401, W0612, F0401
import argparse
import json
import os
import random
import numpy
import neuron

from emodelrunner.load import load_config


def create_cell(path, config):
    """Create the cell model."""
    # Load main cell template
    neuron.h.load_file(os.path.join(path, config.get("Paths", "hoc_file")))

    # Instantiate the cell from the template
    print("Loading cell")
    # has to change current dir for the cell to load synapses if there is any.
    cwd = os.getcwd()
    os.chdir(path)

    template = getattr(neuron.h, neuron.h.template_name)
    cell = template(neuron.h.gid, neuron.h.morph_dir, neuron.h.morph_fname)

    os.chdir(cwd)
    return cell


def create_stimuli(cell, step_number, config):
    """Create the stimuli."""
    # load config
    amps_dir = config.get("Paths", "protocol_amplitudes_dir")
    amps_file = config.get("Paths", "protocol_amplitudes_file")
    stimulus_delay = config.getint("Protocol", "stimulus_delay")
    stimulus_duration = config.getint("Protocol", "stimulus_duration")
    hold_stimulus_delay = config.getint("Protocol", "hold_stimulus_delay")
    hold_stimulus_duration = config.getint("Protocol", "hold_stimulus_duration")

    print("Attaching stimulus electrodes")

    stimuli = []
    step_amp = [0] * 3

    # get current amplitudes
    with open(os.path.join(amps_dir, amps_file), "r") as f:
        data = json.load(f)
    step_amp = data["amps"]
    hyp_amp = data["holding"]

    # step stimulus
    iclamp = neuron.h.IClamp(0.5, sec=cell.soma[0])
    iclamp.delay = stimulus_delay
    iclamp.dur = stimulus_duration
    iclamp.amp = float(step_amp[step_number - 1])
    print(
        "Setting up step current clamp: "
        "amp=%f nA, delay=%f ms, duration=%f ms" % (iclamp.amp, iclamp.delay, iclamp.dur)
    )

    stimuli.append(iclamp)

    # hold stimulus
    hyp_iclamp = neuron.h.IClamp(0.5, sec=cell.soma[0])
    hyp_iclamp.delay = hold_stimulus_delay
    hyp_iclamp.dur = hold_stimulus_duration
    hyp_iclamp.amp = float(hyp_amp)
    print(
        "Setting up hypamp current clamp: "
        "amp=%f nA, delay=%f ms, duration=%f ms"
        % (hyp_iclamp.amp, hyp_iclamp.delay, hyp_iclamp.dur)
    )

    stimuli.append(hyp_iclamp)

    return stimuli


def create_recordings(cell):
    """Create the recordings."""
    print("Attaching recording electrodes")

    recordings = {}

    recordings["time"] = neuron.h.Vector()
    recordings["soma(0.5)"] = neuron.h.Vector()

    recordings["time"].record(neuron.h._ref_t, 0.1)
    recordings["soma(0.5)"].record(cell.soma[0](0.5)._ref_v, 0.1)

    return recordings


def synapses_netstim(cell, config):
    """Synapses stimuli."""
    # load config data
    syn_start = config.getint("Protocol", "syn_start")
    syn_interval = config.getint("Protocol", "syn_interval")
    syn_nmb_of_spikes = config.getint("Protocol", "syn_nmb_of_spikes")
    syn_noise = config.getint("Protocol", "syn_noise")

    persistency_list = []

    # get synapse data
    synapse_list = cell.synapses.synapse_list
    delays = cell.synapses.delays.to_python()
    weights = cell.synapses.weights.to_python()
    synapses = [synapse_list.o(i) for i in range(int(synapse_list.count()))]

    # create synapse stimuli
    for synapse, delay, weight in zip(synapses, delays, weights):
        netstim = neuron.h.NetStim()
        netstim.interval = syn_interval
        netstim.number = syn_nmb_of_spikes
        netstim.start = syn_start
        netstim.noise = syn_noise

        netcon = neuron.h.NetCon(netstim, synapse, -30, delay, weight)

        persistency_list.append(netstim)
        persistency_list.append(netcon)

    return persistency_list


def synapses_vecstim(cell, config):
    """Synapses stimuli."""
    # load config
    vecstim_random = config.get("Protocol", "vecstim_random")
    seed = config.getint("Protocol", "syn_stim_seed")
    syn_start = config.getint("Protocol", "syn_start")
    syn_stop = config.getint("Protocol", "syn_stop")

    persistency_list = []

    # get synapse data
    synapse_list = cell.synapses.synapse_list
    delays = cell.synapses.delays.to_python()
    weights = cell.synapses.weights.to_python()
    synapses = [synapse_list.o(i) for i in range(int(synapse_list.count()))]

    # create random nmb generator
    if vecstim_random == "python":
        random.seed(seed)
    else:
        rand = neuron.h.Random(seed)
        rand.uniform(syn_start, syn_stop)

    # create synapse stimuli
    for synapse, delay, weight in zip(synapses, delays, weights):
        if vecstim_random == "python":
            spike_train = [random.uniform(syn_start, syn_stop)]
        else:
            spike_train = [rand.repick()]
        t_vec = neuron.h.Vector(spike_train)
        vecstim = neuron.h.VecStim()
        vecstim.play(t_vec, neuron.h.dt)
        netcon = neuron.h.NetCon(vecstim, synapse, -30, delay, weight)

        persistency_list.append(t_vec)
        persistency_list.append(vecstim)
        persistency_list.append(netcon)

    return persistency_list


def run_simulation(config):
    """Run step current simulation with index step_number."""
    total_duration = config.getint("Protocol", "total_duration")
    neuron.h.tstop = total_duration

    neuron.h.cvode_active(0)

    print("Running for %f ms" % neuron.h.tstop)
    neuron.h.run()


def save_recordings(recordings, recordings_dir, output_name):
    """Save recordings."""
    time = numpy.array(recordings["time"])
    soma_voltage = numpy.array(recordings["soma(0.5)"])

    soma_voltage_filename = os.path.join(recordings_dir, output_name)
    numpy.savetxt(soma_voltage_filename, numpy.transpose(numpy.vstack((time, soma_voltage))))


def init_simulation(recordings_dir, constants_file):
    """Initialise simulation environment."""
    neuron.h.load_file("stdrun.hoc")
    neuron.h.load_file("import3d.hoc")

    print("Loading constants")
    with open(constants_file, "r") as f:
        data = json.load(f)
    neuron.h("celsius={}".format(data["celsius"]))
    neuron.h("v_init={}".format(data["v_init"]))
    neuron.h("tstop={}".format(data["tstop"]))
    neuron.h("gid={}".format(data["gid"]))
    neuron.h("dt={}".format(data["dt"]))
    neuron.h("strdef template_name, morph_dir, morph_fname")
    neuron.h('template_name="{}"'.format(data["template_name"]))
    neuron.h('morph_dir="{}"'.format(data["morph_dir"]))
    neuron.h('morph_fname="{}"'.format(data["morph_fname"]))

    if not os.path.exists(recordings_dir):
        os.makedirs(recordings_dir)


def main(config_file):
    """Main."""
    # load config
    config = load_config(filename=config_file)

    path = config.get("Paths", "memodel_dir")
    recordings_dir = os.path.join(path, "old_python_recordings")

    step_stimulus = config.getboolean("Protocol", "step_stimulus")

    add_synapses = config.getboolean("Synapses", "add_synapses")
    syn_stim_mode = config.get("Protocol", "syn_stim_mode")

    # init simulation
    constants_path = os.path.join(
        config.get("Paths", "constants_dir"), config.get("Paths", "constants_file")
    )
    init_simulation(recordings_dir, constants_path)

    # create cell
    cell = create_cell(path, config)

    # create recordings
    recordings = create_recordings(cell)

    # add synapses stimuli
    if add_synapses and syn_stim_mode in ["vecstim", "netstim"]:
        if syn_stim_mode == "vecstim":
            _ = synapses_vecstim(cell, config)
        elif syn_stim_mode == "netstim":
            _ = synapses_netstim(cell, config)

    # run simulation
    if step_stimulus:
        for step_number in range(1, 4):
            stimuli = create_stimuli(cell, step_number, config)  # NOQA
            run_simulation(config)
            save_recordings(recordings, recordings_dir, "soma_voltage_step%d.dat" % step_number)
            print(
                "Soma voltage for step %d saved to: %s"
                % (step_number, "soma_voltage_step%d.dat" % step_number)
            )
    else:
        run_simulation(config)
        save_recordings(recordings, recordings_dir, "soma_voltage_%s.dat" % syn_stim_mode)
        print(
            "Soma voltage for %s saved to: %s"
            % (syn_stim_mode, "soma_voltage_%s.dat" % syn_stim_mode)
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--c",
        default=None,
        help="the name of the config file",
    )
    args = parser.parse_args()
    main(args.c)
