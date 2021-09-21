"""Locations related functions and classes."""

import logging

from bluepyopt import ephys

logger = logging.getLogger(__name__)


def multi_locations(sectionlist):
    """Define mechanisms."""
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


class NrnSomaDistanceCompLocation(ephys.locations.NrnSomaDistanceCompLocation):
    """Location at a given distance from soma.

    Parent constructor:
        Args:
            name (str): name of this object
            soma_distance (float): distance from soma to this compartment
            seclist_name (str): name of Neuron section list (ex: 'apical')
    """

    def find_section_at_soma_distance(self, iseclist, sim):
        """Find neuron section at soma distance."""
        for isec in iseclist:
            start_distance = sim.neuron.h.distance(1, 0.0, sec=isec)
            end_distance = sim.neuron.h.distance(1, 1.0, sec=isec)

            min_distance = min(start_distance, end_distance)
            max_distance = max(start_distance, end_distance)

            if min_distance <= self.soma_distance <= end_distance:
                comp_x = float(self.soma_distance - min_distance) / (
                    max_distance - min_distance
                )
                icomp = isec(comp_x)
                seccomp = isec

                logger.info(
                    "Using %s at distance %f, nseg %f, length %f",
                    icomp,
                    sim.neuron.h.distance(1, comp_x, sec=seccomp),
                    seccomp.nseg,
                    end_distance - start_distance,
                )
                return icomp

        return None

    def instantiate(self, sim=None, icell=None):
        """Find the instantiate compartment."""
        soma = icell.soma[0]

        sim.neuron.h.distance(0, 0.5, sec=soma)

        iseclist = getattr(icell, self.seclist_name)

        icomp = self.find_section_at_soma_distance(iseclist, sim)

        if icomp is None:
            raise ephys.locations.EPhysLocInstantiateException(
                f"No comp found at {self.soma_distance} distance from soma"
            )

        return icomp


class NrnSomaDistanceCompLocationApical(NrnSomaDistanceCompLocation):
    """Location in the apical branch at a given distance from soma."""

    def __init__(
        self,
        name,
        soma_distance=None,
        seclist_name=None,
        comment="",
        apical_point_isec=-1,
    ):
        """Constructor."""
        super(NrnSomaDistanceCompLocationApical, self).__init__(
            name, soma_distance, seclist_name, comment
        )
        self.apical_point_isec = apical_point_isec

    def instantiate(self, sim=None, icell=None):
        """Find the instantiate compartment."""
        if self.apical_point_isec == -1:
            raise ephys.locations.EPhysLocInstantiateException(
                "No apical point was given"
            )

        apical_branch = []
        section = icell.apic[self.apical_point_isec]
        while True:
            name = str(section.name()).rsplit(".", maxsplit=1)[-1]
            if name == "soma[0]":
                break
            apical_branch.append(section)

            if sim.neuron.h.SectionRef(sec=section).has_parent():
                section = sim.neuron.h.SectionRef(sec=section).parent
            else:
                raise ephys.locations.EPhysLocInstantiateException(
                    "soma[0] was not reached from apical point"
                )

        soma = icell.soma[0]

        sim.neuron.h.distance(0, 0.5, sec=soma)

        icomp = self.find_section_at_soma_distance(apical_branch, sim)

        if icomp is None:
            raise ephys.locations.EPhysLocInstantiateException(
                f"No comp found at {self.soma_distance} distance from soma"
            )

        return icomp
