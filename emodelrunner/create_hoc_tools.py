"""Creates .hoc from cell."""

# pylint: disable=too-many-arguments
import json
import os
from datetime import datetime

import jinja2

import bluepyopt
from bluepyopt.ephys.create_hoc import (
    _generate_parameters,
    _generate_channels_by_location,
    _generate_reinitrng,
)
from emodelrunner.load import load_amps


def create_run_hoc(template_dir, template_filename, step_stimulus):
    """Returns a string containing run.hoc."""
    # load template
    template_path = os.path.join(template_dir, template_filename)
    with open(template_path) as template_file:
        template = template_file.read()
        template = jinja2.Template(template)

    # edit template
    return template.render(
        step_stimulus=step_stimulus,
    )


def create_synapse_hoc(
    syn_mech_args,
    syn_prot_args,
    syn_hoc_dir,
    template_dir,
    template_filename,
    gid,
    synapses_template_name="synapses",
):
    """Returns a string containing the synapse hoc."""
    # load template
    template_path = os.path.join(template_dir, template_filename)
    with open(template_path) as template_file:
        template = template_file.read()
        template = jinja2.Template(template)

    # edit template
    return template.render(
        TEMPLATENAME=synapses_template_name,
        GID=gid,
        SEED=syn_mech_args["seed"],
        syn_stim_mode=syn_prot_args["syn_stim_mode"],
        syn_interval=syn_prot_args["syn_interval"],
        syn_start=syn_prot_args["syn_start"],
        syn_noise=syn_prot_args["syn_noise"],
        syn_nmb_of_spikes=syn_prot_args["syn_nmb_of_spikes"],
        syn_stop=syn_prot_args["syn_stop"],
        syn_stim_seed=syn_prot_args["syn_stim_seed"],
        rng_settings_mode=syn_mech_args["rng_settings_mode"],
        syn_dir=syn_hoc_dir,
        syn_conf_file=syn_mech_args["syn_conf_file"],
        syn_data_file=syn_mech_args["syn_data_file"],
    )


def create_hoc(
    mechs,
    parameters,
    morphology=None,
    ignored_globals=(),
    replace_axon=None,
    template_name="CCell",
    template_filename="cell_template.jinja2",
    disable_banner=None,
    template_dir=None,
    add_synapses=False,
    synapses_template_name="hoc_synapses",
    syn_hoc_filename="synapses.hoc",
    syn_dir="synapses",
):
    """Return a string containing the hoc template.

    Args:
        mechs (): All the mechs for the hoc template
        parameters (): All the parameters in the hoc template
        morphology (str): Name of morphology
        ignored_globals (iterable str): HOC coded is added for each
        NrnGlobalParameter
        that exists, to test that it matches the values set in the parameters.
        This iterable contains parameter names that aren't checked
        replace_axon (str): String replacement for the 'replace_axon' command.
        Must include 'proc replace_axon(){ ... }
        template_name (str): name of cell class in hoc
        template_filename (str): file name of the jinja2 template
        template_dir (str): dir name of the jinja2 template
        disable_banner (bool): if not True: a banner is added to the hoc file
        add_synapses (bool): if True: synapses are loaded in the hoc
        synapses_template_name (str): synapse class name in hoc
        syn_hoc_filename (str): file name of synapse hoc file
        syn_dir (str): directory where the synapse data /files are
    """
    # pylint: disable=too-many-locals
    if template_dir is None:
        template_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "templates")
        )

    template_path = os.path.join(template_dir, template_filename)
    with open(template_path) as template_file:
        template = template_file.read()
        template = jinja2.Template(template)

    global_params, section_params, range_params, location_order = _generate_parameters(
        parameters
    )
    channels = _generate_channels_by_location(mechs, location_order)

    ignored_global_params = {}
    for ignored_global in ignored_globals:
        if ignored_global in global_params:
            ignored_global_params[ignored_global] = global_params[ignored_global]
            del global_params[ignored_global]

    if not disable_banner:
        banner = "Created by BluePyOpt(%s) at %s" % (
            bluepyopt.__version__,
            datetime.now(),
        )
    else:
        banner = None

    re_init_rng = _generate_reinitrng(mechs)

    return template.render(
        template_name=template_name,
        banner=banner,
        channels=channels,
        morphology=morphology,
        section_params=section_params,
        range_params=range_params,
        global_params=global_params,
        re_init_rng=re_init_rng,
        replace_axon=replace_axon,
        ignored_global_params=ignored_global_params,
        add_synapses=add_synapses,
        synapses_template_name=synapses_template_name,
        syn_hoc_filename=syn_hoc_filename,
        syn_dir=syn_dir,
    )


def create_simul_hoc(
    template_dir,
    template_filename,
    step_args,
    add_synapses,
    syn_stim_mode,
    hoc_paths,
    amps_path,
    constants_path,
    step_stimulus,
    dt=None,
):
    """Create createsimulation.hoc file."""
    # pylint: disable=too-many-locals
    # load config data

    stimulus_duration = step_args["step_duration"]
    stimulus_delay = step_args["step_delay"]
    hold_stimulus_delay = step_args["hold_step_delay"]
    hold_stimulus_duration = step_args["hold_step_duration"]
    total_duration = step_args["total_duration"]

    syn_dir = hoc_paths["syn_dir_for_hoc"]
    syn_hoc_file = hoc_paths["syn_hoc_filename"]
    hoc_file = hoc_paths["hoc_filename"]

    # load data from constants.json
    with open(constants_path, "r") as f:
        data = json.load(f)
    hoc_name = data["template_name"]
    morph_dir = data["morph_dir"]
    morph_fname = data["morph_fname"]
    gid = data["gid"]
    if dt is None:
        dt = data["dt"]
    celsius = data["celsius"]
    v_init = data["v_init"]

    # load data from current_amps
    (amp1, amp2, amp3), holding = load_amps(amps_path)

    # load template
    template_path = os.path.join(template_dir, template_filename)
    with open(template_path) as template_file:
        template = template_file.read()
        template = jinja2.Template(template)

    # edit template
    return template.render(
        step_stimulus=step_stimulus,
        stimulus_duration=stimulus_duration,
        stimulus_delay=stimulus_delay,
        hold_stimulus_delay=hold_stimulus_delay,
        hold_stimulus_duration=hold_stimulus_duration,
        total_duration=total_duration,
        add_synapses=add_synapses,
        syn_stim_mode=syn_stim_mode,
        syn_dir=syn_dir,
        syn_hoc_file=syn_hoc_file,
        hoc_file=hoc_file,
        template_name=hoc_name,
        morph_dir=morph_dir,
        morph_fname=morph_fname,
        gid=gid,
        amp1=amp1,
        amp2=amp2,
        amp3=amp3,
        holding=holding,
        dt=dt,
        celsius=celsius,
        v_init=v_init,
    )
