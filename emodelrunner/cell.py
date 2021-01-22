"""Custom Cell class."""

import logging
import os
import bluepyopt.ephys as ephys

from emodelrunner.create_hoc_tools import create_hoc

logger = logging.getLogger(__name__)


class CellModelCustom(ephys.models.CellModel):
    """Cell model class."""

    def __init__(self, name, morph=None, mechs=None, params=None, gid=0, add_synapses=False):
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
        """
        super(CellModelCustom, self).__init__(name, morph, mechs, params, gid)
        self.add_synapses = add_synapses

    def create_custom_hoc(
        self,
        param_values,
        ignored_globals=(),
        template="cell_template.jinja2",
        disable_banner=False,
        template_dir=None,
        config=None,
        syn_temp_name="hoc_synapses",
    ):
        """Create hoc code for this model."""
        to_unfreeze = []
        for param in self.params.values():
            if not param.frozen:
                param.freeze(param_values[param.name])
                to_unfreeze.append(param.name)

        template_name = self.name
        morphology = os.path.basename(self.morphology.morphology_path)
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

        # remove point process mechanisms
        mechs = []
        for mech in self.mechanisms:
            if not hasattr(mech, "pprocesses"):
                mechs.append(mech)

        syn_dir = config.get("Paths", "syn_dir_for_hoc")
        syn_hoc_filename = config.get("Paths", "syn_hoc_file")

        ret = create_hoc(
            mechs=mechs,
            parameters=self.params.values(),
            morphology=morphology,
            ignored_globals=ignored_globals,
            replace_axon=replace_axon,
            template_name=template_name,
            template_filename=template,
            template_dir=template_dir,
            disable_banner=disable_banner,
            add_synapses=self.add_synapses,
            synapses_template_name=syn_temp_name,
            syn_hoc_filename=syn_hoc_filename,
            syn_dir=syn_dir,
        )

        self.unfreeze(to_unfreeze)

        return ret
