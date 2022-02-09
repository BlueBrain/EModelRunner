"""Custom Morphology classes."""

# Copyright 2020-2022 Blue Brain Project / EPFL

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=unnecessary-comprehension
import logging

from bluepyopt import ephys

logger = logging.getLogger(__name__)


class SSCXNrnFileMorphology(ephys.morphologies.NrnFileMorphology):
    """Custom Morphology.

    Attributes:
        name (str): name of this object
        comment (str): comment
        morphology_path (str): location of the file describing the morphology
        do_replace_axon (bool): Does the axon need to be replaced by an AIS
            stub with default function ?
        replace_axon_hoc (str): Translation in HOC language for the
            'replace_axon' method. This code will 'only' be used when
            calling create_hoc on a cell model. While the model is run in
            python, replace_axon is used instead. Must include
            'proc replace_axon(){ ... }
            If None,the default replace_axon is used
        do_set_nseg (bool): if True, it will use nseg_frequency
        nseg_frequency (float): frequency of nseg
        morph_modifiers (list): list of functions to modify the icell
            with (sim, icell) as arguments
        morph_modifiers_hoc (list): list of hoc strings corresponding
            to morph_modifiers
    """

    def replace_axon(self, sim=None, icell=None):
        """Replace axon.

        Args:
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            icell (neuron cell): cell instantiation in simulator
        """
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


class ThalamusNrnFileMorphology(ephys.morphologies.NrnFileMorphology):
    """Custom Morphology.

    Attributes:
        name (str): name of this object
        comment (str): comment
        morphology_path (str): location of the file describing the morphology
        do_replace_axon (bool): Does the axon need to be replaced by an AIS
            stub with default function ?
        replace_axon_hoc (str): Translation in HOC language for the
            'replace_axon' method. This code will 'only' be used when
            calling create_hoc on a cell model. While the model is run in
            python, replace_axon is used instead. Must include
            'proc replace_axon(){ ... }
            If None,the default replace_axon is used
        do_set_nseg (bool): if True, it will use nseg_frequency
        nseg_frequency (float): frequency of nseg
        morph_modifiers (list): list of functions to modify the icell
            with (sim, icell) as arguments
        morph_modifiers_hoc (list): list of hoc strings corresponding
            to morph_modifiers
    """

    @staticmethod
    def replace_axon(sim=None, icell=None):
        """Replace axon.

        Args:
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            icell (neuron cell): cell instantiation in simulator
        """
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

        # Work-around if axon is too short
        lasti = -2  # Last diam. may be bigger if axon cut

        if len(diams) < nseg_total:
            diams = diams + [diams[lasti]] * (nseg_total - len(diams))
            lens = lens + [lens[lasti]] * (nseg_total - len(lens))
            if nseg_total - len(diams) > 5:
                logger.debug(
                    "Axon too short, adding more than 5 sections with fixed diam"
                )

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

        logger.debug(
            "Replace axon with tapered AIS of length %d, target length was %d, diameters are %s",
            L_real,
            L_target,
            diams,
        )
