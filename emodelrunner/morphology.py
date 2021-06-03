"""Custom Morphology class."""

# pylint: disable=unnecessary-comprehension
import logging
import math
import numpy

import bluepyopt.ephys as ephys

logger = logging.getLogger(__name__)


def get_axon_hoc(replace_axon_hoc):
    """Returns string containing replace axon hoc."""
    with open(replace_axon_hoc, "r") as f:
        return f.read()


class NrnFileMorphologyCustom(ephys.morphologies.NrnFileMorphology):
    """Custom Morphology."""

    def __init__(
        self,
        morphology_path,
        do_replace_axon=False,
        do_set_nseg=True,
        comment="",
        replace_axon_hoc=None,
        do_simplify_morph=False,
    ):
        """Constructor.

        Args:
            morphology_path (str): path to the morphology file
            do_replace_axon (bool): set to True to replace the axon
            do_set_nseg (bool): if True, it will put 40 segments per section
            comment (str) : comment for class heritance
            replace_axon_hoc (str) : hoc script as a string to replace the axon
            do_simplify_morph (bool) : set to True to simplify the morphology
        """
        super(NrnFileMorphologyCustom, self).__init__(
            morphology_path, do_replace_axon, do_set_nseg, comment, replace_axon_hoc
        )

        self.do_simplify_morph = do_simplify_morph

    def instantiate(self, sim=None, icell=None):
        """Load morphology."""
        super(NrnFileMorphologyCustom, self).instantiate(sim, icell)

        if self.do_simplify_morph:
            self.simplify_morph(sim, icell)

    @staticmethod
    def section_area(sim, section):
        """Section area."""
        return sum(sim.neuron.h.area(seg.x, sec=section) for seg in section)

    def cell_area(self, sim):
        """Cell area."""
        total_area = 0
        for section in sim.neuron.h.allsec():
            total_area += self.section_area(sim, section)

        return total_area

    def simplify_morph(self, sim, cell):
        """Simplify morphology."""
        soma = cell.soma[0]

        print(soma.L, soma.diam, self.section_area(sim, soma), self.cell_area(sim))

        soma_children = [x for x in sim.neuron.h.SectionRef(sec=soma).child]
        for soma_child in soma_children:
            if ("axon" not in sim.neuron.h.secname(sec=soma_child)) and (
                "myelin" not in sim.neuron.h.secname(sec=soma_child)
            ):
                self.simplify_children_cross(sim, soma_child, 0)

        sim.neuron.h.topology()
        print(soma.L, soma.diam, self.section_area(sim, soma), self.cell_area(sim))

    def simplify_children_cross(self, sim, parent, level):
        """Simplify parent + children."""
        sparent = sim.neuron.h.SectionRef(sec=parent)
        children = [x for x in sparent.child]

        total_area = self.section_area(sim, parent)
        child_cross_sec = 0

        # DON'T put this in the for loop below ...

        for child in children:
            self.simplify_children_cross(sim, child, level + 1)

            total_area += self.section_area(sim, child)
            child_cross_sec += math.pi * child.diam * child.diam / 4

            sim.neuron.h.delete_section(sec=child)

        parent_cross_sec = math.pi * parent.diam * parent.diam / 4

        if child_cross_sec == 0:
            total_cross_sec = parent_cross_sec
        else:
            total_cross_sec = child_cross_sec

        new_diam = math.sqrt(float(4 * total_cross_sec) / math.pi)

        parent.diam = new_diam

        parent.L = total_area / (math.pi * parent.diam)

        parent.nseg = 1  # + 2 * int(parent.L / 100.)

    def simplify_children_length(self, sim, parent, level):
        """Simplify parent + children."""
        sparent = sim.neuron.h.SectionRef(sec=parent)
        children = [x for x in sparent.child]

        total_area = self.section_area(sim, parent)
        max_child_length = 0
        child_lengths = []

        # DON'T put this in the for loop below ...

        for child in children:
            self.simplify_children_length(sim, child, level + 1)

            total_area += self.section_area(sim, child)

            child_lengths.append(child.L)

            if child.L > max_child_length:
                max_child_length = child.L

            sim.neuron.h.delete_section(sec=child)

        if len(child_lengths) > 0:
            max_child_length = numpy.max(child_lengths)
        else:
            max_child_length = 0

        new_l = parent.L + max_child_length

        parent.L = new_l

        parent.diam = total_area / (math.pi * parent.L)

        parent.nseg = 1 + 2 * int(parent.L / 100.0)

    # @staticmethod
    def set_nseg(self, icell):
        """Set the nseg of every section."""
        if self.do_set_nseg:
            div = 40

            logger.debug("Using set_nseg divider %d", div)

        for section in icell.all:
            section.nseg = 1 + 2 * int(section.L / div)

    def replace_axon(self, sim=None, icell=None):
        """Replace axon."""
        L_target = 60  # length of stub axon
        nseg0 = 5  # number of segments for each of the two axon sections

        nseg_total = nseg0 * 2
        chunkSize = L_target / nseg_total

        diams = []
        lens = []

        count = 0
        for section in icell.axonal:
            L = section.L
            nseg = 1 + int(L / chunkSize / 2.0) * 2  # nseg to get diameter
            section.nseg = nseg

            for seg in section:
                count = count + 1
                diams.append(seg.diam)
                lens.append(L / nseg)
                if count == nseg_total:
                    break
            if count == nseg_total:
                break

        for section in icell.axonal:
            sim.neuron.h.delete_section(sec=section)

        #  new axon array
        sim.neuron.h.execute("create axon[2]", icell)

        L_real = 0
        count = 0

        for section in icell.axon:
            section.nseg = int(nseg_total / 2)
            section.L = L_target / 2

            for seg in section:
                seg.diam = diams[count]
                L_real = L_real + lens[count]
                count = count + 1

            icell.axonal.append(sec=section)
            icell.all.append(sec=section)

        icell.axon[0].connect(icell.soma[0], 1.0, 0.0)
        icell.axon[1].connect(icell.axon[0], 1.0, 0.0)

        sim.neuron.h.execute("create myelin[1]", icell)
        icell.myelinated.append(sec=icell.myelin[0])
        icell.all.append(sec=icell.myelin[0])
        icell.myelin[0].nseg = 5
        icell.myelin[0].L = 1000
        icell.myelin[0].diam = diams[count - 1]
        icell.myelin[0].connect(icell.axon[1], 1.0, 0.0)

        logger.debug(
            "Replace axon with tapered AIS of length %d, target length was %d, diameters are %s",
            L_real,
            L_target,
            diams,
        )
