"""Locations related functions and classes."""

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

logger = logging.getLogger(__name__)


SOMA_LOC = ephys.locations.NrnSeclistCompLocation(
    name="soma", seclist_name="somatic", sec_index=0, comp_x=0.5
)


def multi_locations(sectionlist):
    """Define locations.

    Args:
        sectionlist (str): Name of the location(s) to return.
            Can be alldend, somadend, somaxon, allact, apical, basal, somatic, axonal

    Returns:
        list: locations corresponding to sectionlist
    """
    if sectionlist == "alldend":
        seclist_locs = [
            ephys.locations.NrnSeclistLocation("apical", seclist_name="apical"),
            ephys.locations.NrnSeclistLocation("basal", seclist_name="basal"),
        ]
    elif sectionlist == "somadend":
        seclist_locs = [
            ephys.locations.NrnSeclistLocation("apical", seclist_name="apical"),
            ephys.locations.NrnSeclistLocation("basal", seclist_name="basal"),
            ephys.locations.NrnSeclistLocation("somatic", seclist_name="somatic"),
        ]
    elif sectionlist == "somaxon":
        seclist_locs = [
            ephys.locations.NrnSeclistLocation("axonal", seclist_name="axonal"),
            ephys.locations.NrnSeclistLocation("somatic", seclist_name="somatic"),
        ]
    elif sectionlist == "allact":
        seclist_locs = [
            ephys.locations.NrnSeclistLocation("apical", seclist_name="apical"),
            ephys.locations.NrnSeclistLocation("basal", seclist_name="basal"),
            ephys.locations.NrnSeclistLocation("somatic", seclist_name="somatic"),
            ephys.locations.NrnSeclistLocation("axonal", seclist_name="axonal"),
        ]
    else:
        seclist_locs = [
            ephys.locations.NrnSeclistLocation(sectionlist, seclist_name=sectionlist)
        ]

    return seclist_locs


class NrnSomaDistanceCompLocationApical(ephys.locations.NrnSomaDistanceCompLocation):


    def __init__(self, name, soma_distance=None, seclist_name=None, comment='', apical_sec=None):

        super(NrnSomaDistanceCompLocationApical, self).__init__(name, soma_distance, seclist_name, comment)
        self.apical_sec = apical_sec


    def instantiate(self, sim=None, icell=None):
        """Find the instantiate compartment"""

        apical_branch = []
        section = icell.apic[self.apical_sec]
        while True:
            name = str(section.name()).split('.')[-1]
            if "soma[0]" ==  name:
                break
            apical_branch.append(section)

            if sim.neuron.h.SectionRef(sec=section).has_parent():
                section = sim.neuron.h.SectionRef(sec=section).parent
            else:
                raise Exception(
                    'soma[0] was not reached from apical point')


        soma = icell.soma[0]

        sim.neuron.h.distance(0, 0.5, sec=soma)

        icomp = None

        for isec in apical_branch:
            start_distance = sim.neuron.h.distance(1, 0.0, sec=isec)
            end_distance = sim.neuron.h.distance(1, 1.0, sec=isec)

            min_distance = min(start_distance, end_distance)
            max_distance = max(start_distance, end_distance)

            if min_distance <= self.soma_distance <= end_distance:
                comp_x = float(self.soma_distance - min_distance) / \
                    (max_distance - min_distance)

                icomp = isec(comp_x)
                seccomp = isec

        print('Using %s at distance %f' % (icomp, sim.neuron.h.distance(1, comp_x, sec=seccomp)))

        if icomp is None:
            raise Exception(
                'No comp found at %s distance from soma' %
                self.soma_distance)

        return icomp
