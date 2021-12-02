"""Creates .hoc from cell."""

# Copyright 2020-2021 Blue Brain Project / EPFL

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=too-many-arguments
from datetime import datetime

import jinja2

import bluepyopt
from bluepyopt.ephys.create_hoc import (
    _generate_parameters,
    _generate_channels_by_location,
    _generate_reinitrng,
)


class HocStimuliCreator:
    """Class to create the stimuli in hoc.

    Attributes:
        apical_point_isec (int): section index of the apical point
            Set to -1 if there is no apical point
        n_stims (int): total number of protocols to be run by hoc.
            Gets incremented during initiation to enumerate the protocols.
        max_steps (int): A StepProtocol can have multiple steps. This attribute
            counts the maximum steps that the StepProtocol with the most steps has.
            Stays at 0 if there is no StepProtocol.
        reset_step_stimuli (str): hoc script resetting the step stimuli objects
            to be put inhoc file.
        init_step_stimuli (str): hoc script initiating the step stimuli objects
            to be put in hoc file.
        stims_hoc (str): hoc script containing all the protocols to be run by hoc.
            The Protocols supported by this library to be converted to hoc are:

            - StepProtocol
            - StepThresholdProtocol (only inside  Main Protocol)
            - RampProtocol
            - RampThresholdProtocol (only inside Main Protocol)
            - Vecstim
            - Netstim

        extra_recs_vars (str): names of the extra recordings hoc variables
            Have the form ', var1, var2, ..., var_n' to be added to the hoc variable declaration
        extra_recs (str): hoc script to declare the extra recordings
    """

    def __init__(self, prot_definitions, mtype, add_synapses, apical_point_isec):
        """Get stimuli in hoc to put in createsimulation.hoc.

        Args:
            prot_definitions (dict): dictionary defining the protocols.
                Should have the structure of the protocol file in example/sscx/config/protocols
            mtype (str): mtype of the cell. prefix to use in the output files names
            add_synapses (bool): whether to add synapses to the cell
            apical_point_isec (int): section index of the apical point
                Set to -1 if there is no apical point
        """
        self.apical_point_isec = apical_point_isec
        self.n_stims = 0
        self.max_steps = 0
        self.reset_step_stimuli = ""
        self.init_step_stimuli = ""
        self.stims_hoc = ""
        self.extra_recs_vars = ""
        self.extra_recs = ""
        for prot_name, prot in prot_definitions.items():
            if "extra_recordings" in prot:
                self.add_extra_recs(prot["extra_recordings"])

            # reset stimuli and synapses before every protocol run
            self.stims_hoc += """
                reset_cell()
            """

            if "type" in prot and (
                prot["type"] == "StepProtocol"
                or prot["type"] == "StepThresholdProtocol"
            ):
                self.n_stims += 1
                step_hoc = self.get_step_hoc(prot)
                self.stims_hoc += step_hoc

                self.stims_hoc += """
                    simulate()
                """
                self.stims_hoc += self.add_save_recordings_hoc(mtype, prot_name, prot)

            elif "type" in prot and (
                prot["type"] == "RampProtocol"
                or prot["type"] == "RampThresholdProtocol"
            ):
                self.n_stims += 1
                ramp_hoc = self.get_ramp_hoc(prot)
                self.stims_hoc += ramp_hoc

                self.stims_hoc += """
                    simulate()
                """
                self.stims_hoc += self.add_save_recordings_hoc(mtype, prot_name, prot)

            elif "type" in prot and prot["type"] == "Vecstim" and add_synapses:
                self.n_stims += 1
                vecstim_hoc = self.get_vecstim_hoc(prot)
                self.stims_hoc += vecstim_hoc

                self.stims_hoc += """
                    simulate()
                """
                self.stims_hoc += self.add_save_recordings_hoc(mtype, prot_name, prot)

            elif "type" in prot and prot["type"] == "Netstim" and add_synapses:
                self.n_stims += 1
                netstim_hoc = self.get_netstim_hoc(prot)
                self.stims_hoc += netstim_hoc

                self.stims_hoc += """
                    simulate()
                """
                self.stims_hoc += self.add_save_recordings_hoc(mtype, prot_name, prot)

        self.get_reset_step()
        self.get_init_step()

    def add_extra_recs(self, extra_recs):
        """Add extra recordings to the recordings settings.

        Args:
            extra_recs (list): list of dicts defining the extra recordings
        """
        for extra_rec in extra_recs:
            name = extra_rec["name"]
            seclist_name = extra_rec["seclist_name"]
            var = extra_rec["var"]

            if name not in self.extra_recs_vars.split(", "):
                self.extra_recs_vars += f", {name}"
                if extra_rec["type"] == "nrnseclistcomp":
                    sec_index = extra_rec["sec_index"]
                    comp_x = extra_rec["comp_x"]

                    self.extra_recs += f"""
                        {name} = new Vector()
                        cell.{seclist_name}[{sec_index}] {name}.record(&{var}({comp_x}), 0.1)
                    """
                elif extra_rec["type"] == "somadistance":
                    somadistance = extra_rec["somadistance"]

                    self.extra_recs += f"""
                        {name} = new Vector()
                        secref = find_isec_at_soma_distance(cell.{seclist_name}, {somadistance})
                        comp_x = find_comp_x_at_soma_distance(secref, {somadistance})

                        secref.sec {name}.record(&{var}(comp_x), 0.1)
                    """

                elif extra_rec["type"] == "somadistanceapic":
                    somadistance = extra_rec["somadistance"]

                    self.extra_recs += f"""
                        {name} = new Vector()
                        apical_branch = get_apical_branch({self.apical_point_isec})
                        secref = find_isec_at_soma_distance(apical_branch, {somadistance})
                        comp_x = find_comp_x_at_soma_distance(secref, {somadistance})

                        secref.sec {name}.record(&{var}(comp_x), 0.1)
                    """

    @staticmethod
    def add_save_recordings_hoc(mtype, prot_name, prot):
        """Add this to the hoc file to save the recordings.

        Args:
            mtype (str): mtype of the cell. prefix to use in the output files names
            prot_name (str): name of the protocol. used in the output files names
            prot (dict): dictionary defining the protocol

        Returns:
            str: hoc scipt to save the recordings of given protocol.
        """
        save_recs = f"""
            sprint(fpath.s, "hoc_recordings/{mtype}.{prot_name}.soma.v.dat")
            timevoltage = new Matrix(time.size(), 2)
            timevoltage.setcol(0, time)
            timevoltage.setcol(1, voltage)
            write_output_file(fpath, timevoltage)
        """
        if "extra_recordings" in prot:
            for extra_rec in prot["extra_recordings"]:
                var = extra_rec["var"]
                name = extra_rec["name"]
                save_recs += f"""
                    sprint(fpath.s, "hoc_recordings/{mtype}.{prot_name}.{name}.{var}.dat")
                    timevoltage = new Matrix(time.size(), 2)
                    timevoltage.setcol(0, time)
                    timevoltage.setcol(1, {name})
                    write_output_file(fpath, timevoltage)
                """

        return save_recs

    def get_step_hoc(self, prot):
        """Get step stimuli in hoc format from step protocol dict.

        Args:
            prot (dict): dictionary defining the step protocol

        Returns:
            str: hoc script declaring one or more step stimuli
        """
        step_hoc = ""

        step_definitions = prot["stimuli"]["step"]
        if isinstance(step_definitions, dict):
            step_definitions = [step_definitions]
        for i, step in enumerate(step_definitions):
            if i + 1 > self.max_steps:
                self.max_steps = i + 1

            if step["amp"] is None:
                amp = f"{step['thresh_perc'] / 100.} * threshold_current"
            else:
                amp = step["amp"]

            step_hoc += f"""
                step_stimulus_{i} = new IClamp(0.5)
                step_stimulus_{i}.dur = {step["duration"]}
                step_stimulus_{i}.del = {step["delay"]}
                step_stimulus_{i}.amp = {amp}

                cell.soma step_stimulus_{i}
            """

        step_hoc += f"tstop={step_definitions[0]['totduration']}"

        if "holding" in prot["stimuli"]:
            hold = prot["stimuli"]["holding"]

            if hold["amp"] is None:
                amp = "holding_current"
            else:
                amp = hold["amp"]

            step_hoc += f"""
                holding_stimulus = new IClamp(0.5)
                holding_stimulus.dur = {hold["duration"]}
                holding_stimulus.del = {hold["delay"]}
                holding_stimulus.amp = {amp}

                cell.soma holding_stimulus
            """
        elif prot["type"] == "StepThresholdProtocol":
            step_hoc += f"""
                holding_stimulus = new IClamp(0.5)
                holding_stimulus.dur = {step_definitions[0]['totduration']}
                holding_stimulus.del = 0.0
                holding_stimulus.amp = holding_current

                cell.soma holding_stimulus
            """

        return step_hoc

    @staticmethod
    def get_ramp_hoc(prot):
        """Get ramp stimuli in hoc format from ramp protocol dict.

        Args:
            prot (dict): dictionary defining the ramp protocol

        Returns:
            str: hoc script declaring the ramp stimulus
        """
        ramp_hoc = ""

        ramp_definition = prot["stimuli"]["ramp"]
        # create time and amplitude of stimulus vectors

        if ramp_definition["ramp_amplitude_start"] is None:
            amp_start = (
                f"{ramp_definition['thresh_perc_start'] / 100.} * threshold_current"
            )
        else:
            amp_start = ramp_definition["ramp_amplitude_start"]
        if ramp_definition["ramp_amplitude_end"] is None:
            amp_end = f"{ramp_definition['thresh_perc_end'] / 100.} * threshold_current"
        else:
            amp_end = ramp_definition["ramp_amplitude_end"]

        ramp_hoc += """
            ramp_times = new Vector()
            ramp_amps = new Vector()

            ramp_times.append(0.0)
            ramp_amps.append(0.0)

            ramp_times.append({delay})
            ramp_amps.append(0.0)

            ramp_times.append({delay})
            ramp_amps.append({amplitude_start})

            ramp_times.append({delay} + {duration})
            ramp_amps.append({amplitude_end})

            ramp_times.append({delay} + {duration})
            ramp_amps.append(0.0)

            ramp_times.append({total_duration})
            ramp_amps.append(0.0)
        """.format(
            delay=ramp_definition["ramp_delay"],
            amplitude_start=amp_start,
            duration=ramp_definition["ramp_duration"],
            amplitude_end=amp_end,
            total_duration=ramp_definition["totduration"],
        )
        ramp_hoc += f"""
            ramp_stimulus = new IClamp(0.5)
            ramp_stimulus.dur = {ramp_definition["totduration"]}

            ramp_amps.play(&ramp_stimulus.amp, ramp_times, 1)

            cell.soma ramp_stimulus
        """

        ramp_hoc += f"tstop={ramp_definition['totduration']}"

        if "holding" in prot["stimuli"]:
            hold = prot["stimuli"]["holding"]

            if hold["amp"] is None:
                amp = "holding_current"
            else:
                amp = hold["amp"]

            ramp_hoc += f"""
                holding_stimulus = new IClamp(0.5)
                holding_stimulus.dur = {hold["duration"]}
                holding_stimulus.del = {hold["delay"]}
                holding_stimulus.amp = {amp}

                cell.soma holding_stimulus
            """
        elif prot["type"] == "RampThresholdProtocol":
            ramp_hoc += f"""
                holding_stimulus = new IClamp(0.5)
                holding_stimulus.dur = {ramp_definition['totduration']}
                holding_stimulus.del = 0.0
                holding_stimulus.amp = holding_current

                cell.soma holding_stimulus
            """

        return ramp_hoc

    @staticmethod
    def get_vecstim_hoc(prot):
        """Get vecstim stimulus in hoc format from vecstim protocol dict.

        Args:
            prot (dict): dictionary defining the vecstim protocol

        Returns:
            str: hoc script declaring the vecstim stimuli
        """
        stim = prot["stimuli"]

        vecstim_hoc = f"tstop={stim['syn_stop']}\n"

        hoc_synapse_creation = (
            "cell.synapses.create_netcons "
            + "({mode},{t0},{tf},{itv},{n_spike},{noise},{seed})"
        )
        vecstim_hoc += hoc_synapse_creation.format(
            mode=0,
            t0=stim["syn_start"],
            tf=stim["syn_stop"],
            itv=0,
            n_spike=0,
            noise=0,
            seed=stim["syn_stim_seed"],
        )

        return vecstim_hoc

    @staticmethod
    def get_netstim_hoc(prot):
        """Get netstim stimulus in hoc format from netstim protocol dict.

        Args:
            prot (dict): dictionary defining the netstim protocol

        Returns:
            str: hoc script declaring the netstim simuli
        """
        stim = prot["stimuli"]

        netstim_hoc = f"tstop={stim['syn_stop']}\n"

        hoc_synapse_creation = (
            "cell.synapses.create_netcons"
            + "({mode},{t0},{tf},{itv},{n_spike},{noise},{seed})"
        )
        netstim_hoc += hoc_synapse_creation.format(
            mode=1,
            t0=stim["syn_start"],
            tf=stim["syn_stop"],
            itv=stim["syn_interval"],
            n_spike=stim["syn_nmb_of_spikes"],
            noise=stim["syn_noise"],
            seed=0,
        )

        return netstim_hoc

    def get_reset_step(self):
        """Hoc script reseting all step stimuli needed by all the step protocols."""
        for i in range(max(self.max_steps, 1)):
            self.reset_step_stimuli += """
                step_stimulus_{i} = new IClamp(0.5)
                step_stimulus_{i}.dur = 0.0
                step_stimulus_{i}.del = 0.0
                step_stimulus_{i}.amp = 0.0

                cell.soma step_stimulus_{i}
            """.format(
                i=i
            )

    def get_init_step(self):
        """Hoc script initiating all step stimuli needed by all the step protocols."""
        for i in range(max(self.max_steps, 1)):
            self.init_step_stimuli += f"""
                objref step_stimulus_{i}
            """


def create_run_hoc(template_path, main_protocol):
    """Returns a string containing run.hoc.

    Args:
        template_path (str): path to the template to fill in
        main_protocol (bool): whether the Main Protocol is used or not

    Returns:
        str: hoc script to run the simulation
    """
    # load template
    with open(template_path, "r", encoding="utf-8") as template_file:
        template = template_file.read()
        template = jinja2.Template(template)

    # edit template
    return template.render(
        main_protocol=main_protocol,
    )


def create_synapse_hoc(
    syn_mech_args,
    syn_hoc_dir,
    template_path,
    gid,
    dt,
    synapses_template_name="hoc_synapses",
):
    """Returns a string containing the synapse hoc.

    Args:
        syn_mech_args (dict): synapse-related configuration
        syn_hoc_dir (str): path to directory containing synapse-related data
        template_path (str): path to the template to fill in
        gid (int): cell ID
        dt (float): timestep (ms)
        synapses_template_name (str): template name of the synapse class

    Returns:
        str: hoc script with the synapse class template
    """
    # load template
    with open(template_path, "r", encoding="utf-8") as template_file:
        template = template_file.read()
        template = jinja2.Template(template)

    # edit template
    return template.render(
        TEMPLATENAME=synapses_template_name,
        GID=gid,
        SEED=syn_mech_args["seed"],
        rng_settings_mode=syn_mech_args["rng_settings_mode"],
        syn_dir=syn_hoc_dir,
        syn_conf_file=syn_mech_args["syn_conf_file"],
        syn_data_file=syn_mech_args["syn_data_file"],
        dt=dt,
    )


def create_hoc(
    mechs,
    parameters,
    ignored_globals=(),
    replace_axon=None,
    template_name="CCell",
    template_path="templates/cell_template.jinja2",
    disable_banner=None,
    add_synapses=False,
    synapses_template_name="hoc_synapses",
    syn_hoc_filename="synapses.hoc",
    syn_dir="synapses",
):
    """Return a string containing the hoc template.

    Args:
        mechs (list of bluepyopt.ephys.mechanisms.Mechanisms):
            All the mechs for the hoc template
        parameters (list of bluepyopt.Parameters): All the parameters in the hoc template
        ignored_globals (iterable str): HOC coded is added for each
            NrnGlobalParameter
            that exists, to test that it matches the values set in the parameters.
            This iterable contains parameter names that aren't checked
        replace_axon (str): String replacement for the 'replace_axon' command.
            Must include 'proc replace_axon(){ ... }
        template_name (str): name of cell class in hoc
        template_path (str): path to the jinja2 template
        disable_banner (bool): if not True: a banner is added to the hoc file
        add_synapses (bool): if True: synapses are loaded in the hoc
        synapses_template_name (str): synapse class name in hoc
        syn_hoc_filename (str): file name of synapse hoc file
        syn_dir (str): directory where the synapse data /files are

    Returns:
        str: hoc script describing the cell model
    """
    # pylint: disable=too-many-locals
    with open(template_path, "r", encoding="utf-8") as template_file:
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
        banner = f"Created by BluePyOpt({bluepyopt.__version__}) at {datetime.now()}"
    else:
        banner = None

    re_init_rng = _generate_reinitrng(mechs)

    return template.render(
        template_name=template_name,
        banner=banner,
        channels=channels,
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
    template_path,
    add_synapses,
    hoc_paths,
    constants_args,
    protocol_definitions,
    apical_point_isec=-1,
):
    """Create createsimulation.hoc file.

    Args:
        template_path (str): path to the template to fill in
        add_synapses (bool): whether to add synapses to the cell
        hoc_paths (dict): contains paths of the hoc files to be created
            See load.get_hoc_paths_args for details
        constants_args (dict): contains data about the constants of the simulation
        protocol_definitions (dict): dictionary defining the protocols.
            Should have the structure of the protocol file in example/sscx/config/protocols
        apical_point_isec (int): section index of the apical point
            Set to -1 if there is no apical point

    Returns:
        str: hoc script to create the simulation
    """
    syn_dir = hoc_paths["syn_dir_for_hoc"]
    syn_hoc_file = hoc_paths["syn_hoc_filename"]
    cell_hoc_file = hoc_paths["cell_hoc_filename"]

    hoc_stim_creator = HocStimuliCreator(
        protocol_definitions,
        constants_args["mtype"],
        add_synapses,
        apical_point_isec,
    )

    # load template
    with open(template_path, "r", encoding="utf-8") as template_file:
        template = template_file.read()
        template = jinja2.Template(template)

    # edit template
    return template.render(
        cell_hoc_file=cell_hoc_file,
        add_synapses=add_synapses,
        syn_dir=syn_dir,
        syn_hoc_file=syn_hoc_file,
        celsius=constants_args["celsius"],
        v_init=constants_args["v_init"],
        dt=constants_args["dt"],
        template_name=constants_args["emodel"],
        gid=constants_args["gid"],
        morph_path=constants_args["morph_path"],
        run_simulation=hoc_stim_creator.stims_hoc,
        initiate_step_stimuli=hoc_stim_creator.init_step_stimuli,
        reset_step_stimuli=hoc_stim_creator.reset_step_stimuli,
        extra_recordings_vars=hoc_stim_creator.extra_recs_vars,
        extra_recordings=hoc_stim_creator.extra_recs,
    )


def create_main_protocol_hoc(
    template_path, protocol_definitions, rin_exp_voltage_base, mtype
):
    """Create main_protocol.hoc file.

    Args:
        template_path (str): path to the template to fill in
        protocol_definitions (dict): dictionary defining the protocols
        rin_exp_voltage_base (float): experimental value
            for the voltage_base feature for Rin protocol
        mtype (str): mtype of the cell. prefix to use in the output files names

    Returns:
        str: hoc script containing the main protocol functions
    """
    with open(template_path, "r", encoding="utf-8") as template_file:
        template = template_file.read()
        template = jinja2.Template(template)

    rmp_stim = protocol_definitions["RMP"]["stimuli"]
    rin_stim = protocol_definitions["Rin"]["stimuli"]
    thresh_stim = protocol_definitions["ThresholdDetection"]["step_template"]["stimuli"]

    # edit template
    return template.render(
        rmp_stimulus_dur=rmp_stim["step"]["duration"],
        rmp_stimulus_del=rmp_stim["step"]["delay"],
        rmp_stimulus_amp=rmp_stim["step"]["amp"],
        rmp_stimulus_totduration=rmp_stim["step"]["totduration"],
        rmp_output_path=f"hoc_recordings/{mtype}.RMP.soma.v.dat",
        rin_stimulus_dur=rin_stim["step"]["duration"],
        rin_stimulus_del=rin_stim["step"]["delay"],
        rin_stimulus_amp=rin_stim["step"]["amp"],
        rin_stimulus_totduration=rin_stim["step"]["totduration"],
        rin_holding_dur=rin_stim["holding"]["duration"],
        rin_holding_del=rin_stim["holding"]["delay"],
        holdi_precision=protocol_definitions["RinHoldcurrent"]["holdi_precision"],
        holdi_max_depth=protocol_definitions["RinHoldcurrent"]["holdi_max_depth"],
        voltagebase_exp_mean=rin_exp_voltage_base,
        rin_output_path=f"hoc_recordings/{mtype}.Rin.soma.v.dat",
        holding_current_output_path=f"hoc_recordings/{mtype}.bpo_holding_current.dat",
        thdetect_stimulus_del=thresh_stim["step"]["delay"],
        thdetect_stimulus_dur=thresh_stim["step"]["duration"],
        thdetect_stimulus_totduration=thresh_stim["step"]["totduration"],
        thdetect_holding_dur=thresh_stim["holding"]["duration"],
        thdetect_holding_del=thresh_stim["holding"]["delay"],
        threshold_current_output_path=f"hoc_recordings/{mtype}.bpo_threshold_current.dat",
    )
