"""Stimulus class."""
from bluepyopt.ephys.stimuli import Stimulus


# inspired by bluepyemodel.ecode.sAHP
class Pulse(Stimulus):
    """Train pulse."""

    def __init__(self, location, delay, duration, amp, frequency, width):
        """Constructor.

        Args:
            location(Location): location of stimulus
            delay (float): delay after which the stimuli begin
            duration (float): time at which the stimuli end
            amp (float): amplitude of the stimuli
            frequency (float): frequency of the pulse stimuli
            width (float): width of the step stimuli
        """
        # pylint: disable=super-with-arguments
        self.delay = delay
        self.duration = duration
        self.amp = amp
        self.tpulse = 1000.0 / frequency
        self.width = width
        self.total_duration = self.delay + self.duration

        self.location = location

        self.iclamp = None
        self.current_vec = None
        self.time_vec = None

        super(Pulse, self).__init__()

    def instantiate(self, sim=None, icell=None):
        """Instantiate stimulus."""
        # adaptation from TStim.hoc proc train from neurodamus

        icomp = self.location.instantiate(sim=sim, icell=icell)

        self.iclamp = sim.neuron.h.IClamp(icomp.x, sec=icomp.sec)
        self.iclamp.dur = self.total_duration

        self.current_vec = sim.neuron.h.Vector()
        self.time_vec = sim.neuron.h.Vector()

        if self.width > self.tpulse:
            # one long pulse
            self.time_vec.append(self.delay)
            self.current_vec.append(0)

            self.time_vec.append(self.delay)
            self.current_vec.append(self.amp)

            self.time_vec.append(self.total_duration)
            self.current_vec.append(self.amp)

            self.time_vec.append(self.total_duration)
            self.current_vec.append(0)

        else:
            # repeated pulse injections
            remtime = self.duration
            next_pulse = self.delay

            while remtime > 0:
                if self.width < remtime:
                    self.time_vec.append(next_pulse)
                    self.current_vec.append(0)

                    self.time_vec.append(next_pulse)
                    self.current_vec.append(self.amp)

                    self.time_vec.append(next_pulse + self.width)
                    self.current_vec.append(self.amp)

                    self.time_vec.append(next_pulse + self.width)
                    self.current_vec.append(0)
                else:
                    self.time_vec.append(next_pulse)
                    self.current_vec.append(0)

                    self.time_vec.append(next_pulse)
                    self.current_vec.append(self.amp)

                    self.time_vec.append(self.total_duration)
                    self.current_vec.append(self.amp)

                    self.time_vec.append(self.total_duration)
                    self.current_vec.append(0)

                next_pulse += self.tpulse
                remtime -= self.tpulse

        self.time_vec.append(self.total_duration)
        self.current_vec.append(0)

        self.iclamp.delay = 0
        self.current_vec.play(
            self.iclamp._ref_amp,  # pylint:disable=W0212
            self.time_vec,
            1,
            sec=icomp.sec,
        )

    def destroy(self, sim=None):  # pylint:disable=W0613
        """Destroy stimulus."""
        self.iclamp = None
        self.time_vec = None
        self.current_vec = None


# inspired by bluepyemodel.ecode.sAHP
class MultipleSteps(Stimulus):
    """Multiple steps protocol at custom times."""

    def __init__(self, location, starts, amp, width):
        """Constructor.

        Args:
            location(Location): location of stimulus
            starts (list): times at which each step occurs
            amp (float): amplitude of the stimuli
            width (float): width of the step stimuli
        """
        # pylint: disable=super-with-arguments
        self.starts = starts
        self.amp = amp
        self.width = width
        self.total_duration = self.starts[-1] + self.width

        self.location = location

        self.iclamp = None
        self.current_vec = None
        self.time_vec = None

        super(MultipleSteps, self).__init__()

    def instantiate(self, sim=None, icell=None):
        """Instantiate stimulus."""
        # adaptation from TStim.hoc proc train from neurodamus

        icomp = self.location.instantiate(sim=sim, icell=icell)

        self.iclamp = sim.neuron.h.IClamp(icomp.x, sec=icomp.sec)
        self.iclamp.dur = self.total_duration

        self.current_vec = sim.neuron.h.Vector()
        self.time_vec = sim.neuron.h.Vector()

        for start in self.starts:
            self.time_vec.append(start)
            self.current_vec.append(0)

            self.time_vec.append(start)
            self.current_vec.append(self.amp)

            self.time_vec.append(start + self.width)
            self.current_vec.append(self.amp)

            self.time_vec.append(start + self.width)
            self.current_vec.append(0)

        self.time_vec.append(self.total_duration)
        self.current_vec.append(0)

        self.iclamp.delay = 0
        self.current_vec.play(
            self.iclamp._ref_amp,  # pylint:disable=W0212
            self.time_vec,
            1,
            sec=icomp.sec,
        )

    def destroy(self, sim=None):  # pylint:disable=W0613
        """Destroy stimulus."""
        self.iclamp = None
        self.time_vec = None
        self.current_vec = None
