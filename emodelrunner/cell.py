"""Custom Cell class."""

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

import logging
from bluepyopt import ephys

from emodelrunner.create_hoc_tools import create_hoc

logger = logging.getLogger(__name__)


class CellModelCustom(ephys.models.CellModel):
    """Cell model class.

    Attributes:
        name (str): name of the model
        morphology (bluepyopt.ephys.morphologies.Morphology):
            underlying Morphology of the cell
        mechanisms (list of bluepyopt.ephys.mechanisms.Mechanisms):
            Mechanisms associated with the cell
        params (collections.OrderedDict of bluepyopt.Parameters): Parameters of the cell model
        icell (neuron cell): Cell instantiation in simulator
        param_values (dict): contains values of the optimized parameters
        gid (int): cell's ID
        seclist_names (list of strings): Names of the lists of sections
        secarray_names (list of strings): Names of the sections
        add_synapses (bool): set to True to add synapses to the cell
        fixhp (bool): to uninsert SK_E2 for hyperpolarization
    """

    def __init__(
        self,
        name,
        morph=None,
        mechs=None,
        params=None,
        gid=0,
        add_synapses=False,
        fixhp=False,
    ):
        """Constructor.

        Args:
            name (str): name of this object
                        should be alphanumeric string, underscores are allowed,
                        first char should be a letter
            morph (Morphology): underlying Morphology of the cell
            mechs (list of Mechanisms): Mechanisms associated with the cell
            params (list of Parameters): Parameters of the cell model
            gid (int): id of cell
            add_synapses (bool): set to True to add synapses to the cell
            fixhp (bool): to uninsert SK_E2 for hyperpolarization
        """
        super(CellModelCustom, self).__init__(name, morph, mechs, params, gid)
        self.add_synapses = add_synapses
        self.fixhp = fixhp

    def get_replace_axon(self):
        """Return appropriate replace_axon str.

        Returns:
            str: hoc script defining the replacement axon
        """
        if self.morphology.do_replace_axon:
            replace_axon = self.morphology.replace_axon_hoc
        else:
            replace_axon = None

        if (
            self.morphology.morph_modifiers is not None
            and self.morphology.morph_modifiers_hoc is None
        ):
            logger.warning(
                "You have provided custom morphology modifiers, \
                            but no corresponding hoc files."
            )
        elif (
            self.morphology.morph_modifiers is not None
            and self.morphology.morph_modifiers_hoc is not None
        ):
            if replace_axon is None:
                replace_axon = ""
            for morph_modifier_hoc in self.morphology.morph_modifiers_hoc:
                replace_axon += "\n"
                replace_axon += morph_modifier_hoc

        return replace_axon

    def freeze_params(self, param_values):
        """Freeze params and return list of params to unfreze afterwards.

        Args:
            param_values (dict): contains values of the optimized parameters

        Returns:
            list: names of the newly frozen parameters
        """
        to_unfreeze = []
        for param in self.params.values():
            if not param.frozen:
                param.freeze(param_values[param.name])
                to_unfreeze.append(param.name)

        return to_unfreeze

    def remove_point_process_mechs(self):
        """Return mechanisms without point process mechanisms.

        Returns:
            list of Mechanisms without the point process mechanisms
        """
        mechs = []
        for mech in self.mechanisms:
            if not hasattr(mech, "pprocesses"):
                mechs.append(mech)

        return mechs

    def create_custom_hoc(
        self,
        param_values,
        ignored_globals=(),
        template_path="templates/cell_template.jinja2",
        disable_banner=False,
        syn_dir=None,
        syn_hoc_filename=None,
        syn_temp_name="hoc_synapses",
    ):
        """Create hoc code for this model.

        Args:
            param_values (dict): contains values of the optimized parameters
            ignored_globals (iterable str): HOC coded is added for each
                NrnGlobalParameter that exists, to test that it matches the values
                set in the parameters.
                This iterable contains parameter names that aren't checked
            template_path (str): path to the jinja2 template
            disable_banner (bool): if not True: a banner is added to the hoc file
            syn_dir (str): directory where the synapse data /files are
            syn_hoc_filename (str): file name of synapse hoc file
            syn_temp_name (str): synapse class name in hoc

        Returns:
            str: hoc script describing this cell model
        """
        # pylint: disable=too-many-arguments
        to_unfreeze = self.freeze_params(param_values)

        replace_axon = self.get_replace_axon()

        mechs = self.remove_point_process_mechs()

        ret = create_hoc(
            mechs=mechs,
            parameters=self.params.values(),
            ignored_globals=ignored_globals,
            replace_axon=replace_axon,
            template_name=self.name,
            template_path=template_path,
            disable_banner=disable_banner,
            add_synapses=self.add_synapses,
            synapses_template_name=syn_temp_name,
            syn_hoc_filename=syn_hoc_filename,
            syn_dir=syn_dir,
        )

        self.unfreeze(to_unfreeze)

        return ret

    @staticmethod
    def connectable_empty_cell_template(
        template_name,
        seclist_names=None,
        secarray_names=None,
    ):
        """Create a hoc script of an empty cell with an additional connection function.

        Args:
            template_name (str): name of the cell model
            seclist_names (list of strings): Names of the lists of sections
            secarray_names (list of strings): Names of the sections

        Returns:
            str: hoc script describing an empty cell model with connection function
        """
        objref_str = "objref this, CellRef"
        newseclist_str = ""

        if seclist_names:
            for seclist_name in seclist_names:
                objref_str += f", {seclist_name}"
                newseclist_str += f"             {seclist_name} = new SectionList()\n"

        secarrays_str = ""
        if secarray_names:
            secarrays_str = "create "
            secarrays_str += ", ".join(
                f"{secarray_name}[1]" for secarray_name in secarray_names
            )
            secarrays_str += "\n"

        template = """\
        begintemplate %(template_name)s
          %(objref_str)s
          public init, getCell, getCCell, connect2target
          public soma, dend, apic, axon, myelin
          %(secarrays_str)s

          obfunc getCell(){
            return this
          }
          obfunc getCCell(){
            return CellRef
          }

          /*!
          * @param $o1 NetCon source (can be nil)
          * @param $o2 Variable where generated NetCon will be placed
          */
          proc connect2target() { //$o1 target point process, $o2 returned NetCon
            soma $o2 = new NetCon(&v(1), $o1)
            $o2.threshold = -30
          }

          proc init() {\n%(newseclist_str)s
            forall delete_section()
            CellRef = this
          }

          gid = 0

          proc destroy() {localobj nil
            CellRef = nil
          }


        endtemplate %(template_name)s
               """ % dict(
            template_name=template_name,
            objref_str=objref_str,
            newseclist_str=newseclist_str,
            secarrays_str=secarrays_str,
        )
        return template

    def create_empty_cell(self, name, sim, seclist_names=None, secarray_names=None):
        """Create an empty cell in Neuron.

        Args:
            template_name (str): name of the cell model
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            seclist_names (list of strings): Names of the lists of sections
            secarray_names (list of strings): Names of the sections

        Returns:
            Cell instantiation in simulator
        """
        hoc_template = self.connectable_empty_cell_template(
            name, seclist_names, secarray_names
        )
        sim.neuron.h(hoc_template)

        template_function = getattr(sim.neuron.h, name)

        return template_function()

    def instantiate(self, sim=None):
        """Instantiate model in simulator.

        Args:
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
        """
        # pylint: disable=unnecessary-comprehension
        super(CellModelCustom, self).instantiate(sim)

        # Hyperpolarization workaround
        somatic = [x for x in self.icell.somatic]
        axonal = [x for x in self.icell.axonal]
        if self.fixhp:
            for sec in somatic + axonal:
                sec.uninsert("SK_E2")
