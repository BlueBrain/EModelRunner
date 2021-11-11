"""Protocols."""

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

# pylint: disable=too-many-lines

import collections
import copy
import logging
import numpy as np

from bluepyopt import ephys

logger = logging.getLogger(__name__)


class ProtocolMixin:
    """Contains methods useful for multiple Protocol classes."""

    def curr_output_key(self):
        """Get the output key for current based on the one for voltage.

        Returns:
            str used as key in current dict
        """
        if self.recordings is not None:
            # this gives 'prefix.name'
            name = ".".join(self.recordings[0].name.split(".")[:2])
        else:
            name = ""
        return "current_" + name


class RatSSCxMainProtocol(ephys.protocols.Protocol):
    """Main protocol to fit RatSSCx neuron ephys parameters.

    Pseudo code:

    - Find resting membrane potential
    - Find input resistance
    - Run other protocols:

      - Find holding current
      - Find rheobase
      - Run IDRest
      - Possibly run other protocols (based on constructor arguments)
      - Return all the responses

    Attributes:
        name (str): name of the protocol
        rmp_protocol (StepProtocol): resting membrane potential protocol
        rmp_efeature (bluepyopt.ephys.efeatures.eFELFeature): voltage base efeature
        rinhold_protocol (RatSSCxRinHoldcurrentProtocol): protocol to get the holding current
        rin_efeature (bluepyopt.ephys.efeatures.eFELFeature): ohmic input resistance vb ssse
        thdetect_protocol (RatSSCxThresholdDetectionProtocol): protocol to detect threshold current
        other_protocols (bluepyopt.ephys.protocols.Protocol): other protocols to run
        pre_protocols (bluepyopt.ephys.protocols.Protocol):
            protocols to run before the 'other protocols'
    """

    def __init__(
        self,
        name,
        rmp_protocol=None,
        rmp_efeature=None,
        rinhold_protocol=None,
        rin_efeature=None,
        thdetect_protocol=None,
        other_protocols=None,
        pre_protocols=None,
    ):
        """Constructor.

        Args:
            name (str): name of the protocol
            rmp_protocol (StepProtocol): resting membrane potential protocol
            rmp_efeature (bluepyopt.ephys.efeatures.eFELFeature): voltage base efeature
            rinhold_protocol (RatSSCxRinHoldcurrentProtocol): protocol to get the holding current
            rin_efeature (bluepyopt.ephys.efeatures.eFELFeature): ohmic input resistance vb ssse
            thdetect_protocol (RatSSCxThresholdDetectionProtocol): protocol to detect
                threshold current
            other_protocols (bluepyopt.ephys.protocols.Protocol): other protocols to run
            pre_protocols (bluepyopt.ephys.protocols.Protocol): protocols to run
                before the 'other protocols'
        """
        # pylint: disable=too-many-arguments
        super(RatSSCxMainProtocol, self).__init__(name=name)

        self.rmp_protocol = rmp_protocol
        self.rmp_efeature = rmp_efeature

        self.rinhold_protocol = rinhold_protocol
        self.rin_efeature = rin_efeature

        self.thdetect_protocol = thdetect_protocol
        self.other_protocols = other_protocols

        self.pre_protocols = pre_protocols

    def subprotocols(self):
        """Return all the subprotocols contained in this protocol, is recursive.

        Returns:
            dict containing all the subprotocols
        """
        subprotocols = collections.OrderedDict({self.name: self})
        subprotocols.update(self.rmp_protocol.subprotocols())
        subprotocols.update(self.rinhold_protocol.subprotocols())
        subprotocols.update(self.thdetect_protocol.subprotocols())
        for other_protocol in self.other_protocols:
            subprotocols.update(other_protocol.subprotocols())
        for pre_protocol in self.pre_protocols:
            subprotocols.update(pre_protocol.subprotocols())

        return subprotocols

    @property
    def rin_efeature(self):
        """Get rin_efeature.

        Returns:
            rin_efeature (bluepyopt.ephys.efeatures.eFELFeature): ohmic input resistance vb ssse
        """
        return self.rinhold_protocol.rin_efeature

    @rin_efeature.setter
    def rin_efeature(self, value):
        """Set rin_efeature."""
        self.rinhold_protocol.rin_efeature = value

    def run_pre_protocols(self, responses, cell_model, sim):
        """Run the pre-protocols.

        Args:
            responses (dict): responses to be updated
            cell_model (bluepyopt.ephys.models.CellModel): the cell on which
                to apply the pre protocols
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
        """
        for pre_protocol in self.pre_protocols:
            response = pre_protocol.run(cell_model, {}, sim=sim)
            responses.update(response)

    def run_other_protocols(self, responses, cell_model, sim):
        """Run other protocols.

        Args:
            responses (dict): responses to be updated
            cell_model (bluepyopt.ephys.models.CellModel): the cell on which
                to apply the other protocols
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
        """
        for other_protocol in self.other_protocols:
            response = other_protocol.run(cell_model, {}, sim=sim)
            responses.update(response)

    def run(self, cell_model, param_values, sim=None, isolate=None):
        """Run protocol.

        Args:
            cell_model (bluepyopt.ephys.models.CellModel): the cell model
            param_values (dict): optimized parameters
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            isolate (bool): whether to isolate the run in a process with a timeout
                to avoid bad cells running for too long

        Returns:
            dict containing the responses for all the protocols
        """
        # pylint: disable=unused-argument
        responses = collections.OrderedDict()

        cell_model.freeze(param_values)

        # Find resting membrane potential
        rmp_response = self.rmp_protocol.run(cell_model, {}, sim=sim)
        responses.update(rmp_response)
        rmp = self.rmp_efeature.calculate_feature(rmp_response)

        # Find Rin and holding current
        rinhold_response = self.rinhold_protocol.run(cell_model, {}, sim=sim, rmp=rmp)
        holding_current = cell_model.holding_current

        if rinhold_response is not None:
            rin = self.rin_efeature.calculate_feature(rinhold_response)
            responses.update(rinhold_response)

            responses.update(
                self.thdetect_protocol.run(
                    cell_model,
                    sim=sim,
                    holdi=holding_current,
                    rin=rin,
                )
            )

            if cell_model.threshold_current is not None:
                self.run_pre_protocols(responses, cell_model, sim)
                self.run_other_protocols(responses, cell_model, sim)

        cell_model.unfreeze(param_values.keys())

        return responses

    def generate_current(self, threshold_current=None, holding_current=None, dt=0.1):
        """Generate current for all protocols except rin and threshold detection.

        Args:
            threshold_current (float): the threshold current (nA)
            holding_current (float): the holding current (nA)
            dt (float): timestep of the generated currents (ms)

        Returns:
            dict containing the generated currents
        """
        currents = {}

        # rmp is step protocol
        currents.update(
            self.rmp_protocol.generate_current(
                threshold_current=threshold_current,
                holding_current=holding_current,
                dt=dt,
            )
        )

        for pre_protocol in self.pre_protocols:
            currents.update(
                pre_protocol.generate_current(
                    threshold_current=threshold_current,
                    holding_current=holding_current,
                    dt=dt,
                )
            )

        for other_protocol in self.other_protocols:
            currents.update(
                other_protocol.generate_current(
                    threshold_current=threshold_current,
                    holding_current=holding_current,
                    dt=dt,
                )
            )

        return currents


class RatSSCxRinHoldcurrentProtocol(ephys.protocols.Protocol):
    """IDRest protocol to fit RatSSCx neuron ephys parameters.

    Attributes:
        name (str): name of the protocol
        rin_protocol_template (StepProtocol): template for Rin protocol
            with amplitude for the holding stimulus to be filled
        voltagebase_efeature (bluepyopt.ephys.efeatures.eFELFeature): voltage base efeature
        holdi_estimate_multiplier (float): when searching for holding current amplitude,
            multiply holding current estimate by this value to get lower bound
        holdi_precision (float): precision with which to reach holding voltage when searching
            for holding current
        holdi_max_depth (int): maximum number of times to compute the holding voltage
            when searching for holding current if holdi_precision is not reached
        prefix (str): prefix used in naming responses, features, recordings, etc.
        rin_efeature (bluepyopt.ephys.efeatures.eFELFeature): ohmic input resistance vb ssse
        rin_protocol (StepProtocol): Rin protocol with holding current amplitude
    """

    def __init__(
        self,
        name,
        rin_protocol_template=None,
        voltagebase_efeature=None,
        holdi_estimate_multiplier=2,
        holdi_precision=0.1,
        holdi_max_depth=5,
        prefix=None,
    ):
        """Constructor.

        Args:
            name (str): name of the protocol
            rin_protocol_template (StepProtocol): template for Rin protocol
                with amplitude for the holding stimulus to be filled
            voltagebase_efeature (bluepyopt.ephys.efeatures.eFELFeature): voltage base efeature
            holdi_estimate_multiplier (float): when searching for holding current amplitude,
                multiply holding current estimate by this value to get lower bound
            holdi_precision (float): precision with which to reach holding voltage when searching
                for holding current
            holdi_max_depth (int): maximum number of times to compute the holding voltage
                when searching for holding current if holdi_precision is not reached
            prefix (str): prefix used in naming responses, features, recordings, etc.
        """
        # pylint: disable=too-many-arguments
        super(RatSSCxRinHoldcurrentProtocol, self).__init__(name=name)
        self.rin_protocol_template = rin_protocol_template
        self.voltagebase_efeature = voltagebase_efeature
        self.holdi_estimate_multiplier = holdi_estimate_multiplier
        self.holdi_precision = holdi_precision
        self.holdi_max_depth = holdi_max_depth

        if prefix is None:
            self.prefix = ""
        else:
            self.prefix = prefix + "."

        # this will be set before the run through main protocol setter
        self.rin_efeature = None

        # This will be set after the run()
        self.rin_protocol = None

    def run(self, cell_model, param_values, sim, rmp=None):
        """Run protocol.

        Args:
            cell_model (bluepyopt.ephys.models.CellModel): the cell model
            param_values (dict): optimized parameters
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            rmp (float): resting membrane potential (mV)

        Returns:
            dict containing the responses for the Rin protocol using holding current
        """
        responses = collections.OrderedDict()

        # Calculate Rin without holding current
        rin_noholding_protocol = self.create_rin_protocol(holdi=0)
        rin_noholding_response = rin_noholding_protocol.run(
            cell_model, param_values, sim=sim
        )
        rin_noholding = self.rin_efeature.calculate_feature(rin_noholding_response)

        # Search holding current
        holdi = self.search_holdi(
            cell_model,
            param_values,
            sim,
            self.voltagebase_efeature.exp_mean,
            rin_noholding,
            rmp,
        )

        if holdi is None:
            return None

        # Set up Rin protocol
        self.rin_protocol = self.create_rin_protocol(holdi=holdi)

        # Return response
        responses = self.rin_protocol.run(cell_model, param_values, sim)

        responses[self.prefix + "bpo_holding_current"] = holdi

        cell_model.holding_current = holdi

        return responses

    def subprotocols(self):
        """Return subprotocols.

        Returns:
            dict containing the Rin protocol and the Rin protocol template
        """
        subprotocols = collections.OrderedDict({self.name: self})

        subprotocols.update(
            {self.rin_protocol_template.name: self.rin_protocol_template}
        )

        return subprotocols

    def create_rin_protocol(self, holdi=None):
        """Create threshold protocol.

        Args:
            holdi (float): amplitude of holding current (nA)

        Returns:
            StepProtocol: the Rin protocol with holding current
        """
        rin_protocol = copy.deepcopy(self.rin_protocol_template)
        rin_protocol.name = "Rin"
        for recording in rin_protocol.recordings:
            recording.name = recording.name.replace(
                self.rin_protocol_template.name, rin_protocol.name
            )

        rin_protocol.holding_stimulus.step_amplitude = holdi

        return rin_protocol

    def search_holdi(
        self, cell_model, param_values, sim, holding_voltage, rin_noholding, rmp
    ):
        """Find the holding current to hold cell at holding_voltage.

        Args:
            cell_model (bluepyopt.ephys.models.CellModel): the cell model
            param_values (dict): optimized parameters
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            holding_voltage (float): experimental mean of the voltage base efeature (mV)
            rin_noholding (float): Rin efeature (ohmic input resistance vb ssse) value
                when no holding current is applied (mV/nA)
            rmp (float): resting membrane potential (mV)

        Returns:
            float: the holding current (nA) that reproduces the experimental holding voltage
        """
        holdi_estimate = float(holding_voltage - rmp) / rin_noholding

        upper_bound = 0.0
        lower_bound = self.holdi_estimate_multiplier * holdi_estimate
        middle_bound = upper_bound - abs(upper_bound - lower_bound) / 2
        middle_voltage = self.voltage_base(
            middle_bound, cell_model, param_values, sim=sim
        )

        n = 0
        while (
            abs(middle_voltage - holding_voltage) > self.holdi_precision
            and n < self.holdi_max_depth
        ):
            if middle_voltage > holding_voltage:
                upper_bound = middle_bound
            else:
                lower_bound = middle_bound
            middle_bound = upper_bound - abs(upper_bound - lower_bound) / 2
            middle_voltage = self.voltage_base(
                middle_bound, cell_model, param_values, sim=sim
            )
            n += 1

        return middle_bound

    def voltage_base(self, current, cell_model, param_values, sim=None):
        """Calculate voltage base for certain stimulus current.

        Args:
            current (float): amplitude of the holding current to inject (nA)
            cell_model (bluepyopt.ephys.models.CellModel): the cell model
            param_values (dict): optimized parameters
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator

        Returns:
            float: voltage base (mV) of response
        """
        protocol = self.create_rin_protocol(holdi=current)

        response = protocol.run(cell_model, param_values, sim=sim)

        feature = ephys.efeatures.eFELFeature(
            name="Holding.voltage_base",
            efel_feature_name="voltage_base",
            recording_names={"": self.prefix + "Rin.soma.v"},
            stim_start=protocol.stim_start,
            stim_end=protocol.stim_end,
            exp_mean=0,
            exp_std=0.1,
        )

        voltage_base = feature.calculate_feature(response)

        return voltage_base


class RatSSCxThresholdDetectionProtocol(ephys.protocols.Protocol):
    """IDRest protocol to fit RatSSCx neuron ephys parameters.

    Attributes:
        name (str): name of the protocol
        step_protocol_template (StepProtocol): template for threshold protocol
            with amplitude for the holding and steps stimuli to be filled
        max_threshold_voltage (float): Use this (mV) to get max threshold current upper bound
            when searching for threshold current
        short_perc (float): multiply step duration by this value
            when detecting spikes with short stimulus. Should be < 1.
            Not actually a percentage (0.1 -> 10%)
        short_steps (int): the number of short steps to perform to determine
            the upper bound of the threshold search with long steps
        holding_voltage (float): experimental mean of the voltage base efeature (mV)
            of the Rin protocol
        prefix (str): prefix used in naming responses, features, recordings, etc.
    """

    def __init__(
        self,
        name,
        step_protocol_template=None,
        max_threshold_voltage=-40,
        holding_voltage=None,
        prefix=None,
    ):
        """Constructor.

        Args:
            name (str): name of the protocol
            step_protocol_template (StepProtocol): template for threshold protocol
                with amplitude for the holding and steps stimuli to be filled
            max_threshold_voltage (float): Use this (mV) to get max threshold current upper bound
                when searching for threshold current
            holding_voltage (float): experimental mean of the voltage base efeature (mV)
                of the Rin protocol
            prefix (str): prefix used in naming responses, features, recordings, etc.
        """
        super(RatSSCxThresholdDetectionProtocol, self).__init__(name=name)

        self.step_protocol_template = step_protocol_template
        self.max_threshold_voltage = max_threshold_voltage

        self.short_perc = 0.1
        self.short_steps = 20
        self.holding_voltage = holding_voltage

        if prefix is None:
            self.prefix = ""
        else:
            self.prefix = prefix + "."

    def subprotocols(self):
        """Return subprotocols.

        Returns:
            dict: the threshold detection protocol and the threshold detection protocol template
        """
        subprotocols = collections.OrderedDict({self.name: self})

        subprotocols.update(self.step_protocol_template.subprotocols())

        return subprotocols

    def run(self, cell_model, sim, holdi, rin):
        """Run protocol.

        Args:
            cell_model (bluepyopt.ephys.models.CellModel): the cell model
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            holdi (float): holding current amplitude (nA)
            rin (float): Rin efeature (ohmic input resistance vb ssse) value (mV/nA)

        Returns:
            dict containing threshold current
        """
        responses = collections.OrderedDict()

        # Calculate max threshold current
        max_threshold_current = self.max_threshold_current(rin=rin)

        # Calculate spike threshold
        threshold_current = self.search_spike_threshold(
            cell_model,
            {},
            holdi=holdi,
            lower_bound=-holdi,
            upper_bound=max_threshold_current,
            sim=sim,
        )

        cell_model.threshold_current = threshold_current

        responses[self.prefix + "bpo_threshold_current"] = threshold_current

        return responses

    def max_threshold_current(self, rin=None):
        """Find the current necessary to get to max_threshold_voltage.

        Args:
            rin (float): Rin efeature (ohmic input resistance vb ssse) value (mV/nA)

        Returns:
            float: maximum threshold current (nA)
        """
        max_threshold_current = (
            float(self.max_threshold_voltage - self.holding_voltage) / rin
        )

        logger.info("Max threshold current: %.6g", max_threshold_current)

        return max_threshold_current

    def create_step_protocol(self, holdi=0.0, step_current=0.0):
        """Create threshold protocol.

        Args:
            holdi (float): holding current amplitude (nA)
            step_current (float): step current amplitude (nA)

        Returns:
            StepProtocol: the threshold protocol
        """
        threshold_protocol = copy.deepcopy(self.step_protocol_template)
        threshold_protocol.name = "Threshold"
        for recording in threshold_protocol.recordings:
            recording.name = recording.name.replace(
                self.step_protocol_template.name, threshold_protocol.name
            )

        if threshold_protocol.holding_stimulus is not None:
            threshold_protocol.holding_stimulus.step_amplitude = holdi

        for step_stim in threshold_protocol.step_stimuli:
            step_stim.step_amplitude = step_current

        return threshold_protocol

    def create_short_threshold_protocol(self, holdi=None, step_current=None):
        """Create short threshold protocol.

        Args:
            holdi (float): holding current amplitude (nA)
            step_current (float): step current amplitude (nA)

        Returns:
            StepProtocol: the threshold protocol with shorter step duration and total duration
        """
        short_protocol = self.create_step_protocol(
            holdi=holdi, step_current=step_current
        )
        origin_step_duration = short_protocol.stim_duration
        origin_step_delay = short_protocol.stim_start

        short_step_duration = origin_step_duration * self.short_perc
        short_total_duration = origin_step_delay + short_step_duration

        short_protocol.step_stimuli[0].step_duration = short_step_duration
        short_protocol.step_stimuli[0].total_duration = short_total_duration

        if short_protocol.holding_stimulus is not None:
            short_protocol.holding_stimulus.step_duration = short_total_duration
            short_protocol.holding_stimulus.total_duration = short_total_duration

        return short_protocol

    def detect_spike(
        self,
        cell_model,
        param_values,
        sim=None,
        step_current=None,
        holdi=None,
        short=False,
    ):
        """Detect if spike is present at current level.

        Args:
            cell_model (bluepyopt.ephys.models.CellModel): the cell model
            param_values (dict): optimized parameters
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            step_current (float): step current amplitude (nA)
            holdi (float): holding current amplitude (nA)
            short (bool): whether the protocol step duration should be shorten

        Returns:
            bool: True if at least one spike was detected, False otherwise
        """
        # Only run short pulse if percentage set smaller than 100%
        if short and self.short_perc < 1.0:
            protocol = self.create_short_threshold_protocol(
                holdi=holdi, step_current=step_current
            )
        else:
            protocol = self.create_step_protocol(holdi=holdi, step_current=step_current)

        response = protocol.run(cell_model, param_values, sim=sim)

        feature = ephys.efeatures.eFELFeature(
            name="ThresholdDetection.Spikecount",
            efel_feature_name="Spikecount",
            recording_names={"": self.prefix + "ThresholdDetection.soma.v"},
            stim_start=protocol.stim_start,
            stim_end=protocol.stim_end,
            exp_mean=1,
            exp_std=0.1,
        )

        spike_count = feature.calculate_feature(response)

        return spike_count >= 1

    def search_spike_threshold(
        self,
        cell_model,
        param_values,
        sim=None,
        holdi=None,
        lower_bound=None,
        upper_bound=None,
        precision=0.01,
        max_depth=5,
    ):
        """Find the current step spiking threshold.

        Args:
            cell_model (bluepyopt.ephys.models.CellModel): the cell model
            param_values (dict): optimized parameters
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            holdi (float): holding current amplitude (nA)
            lower_bound (float): lower bound in which to search for threshold current (nA)
            upper_bound (float): upper bound in which to search for threshold current (nA)
            precision (float): precision with which to compute threshold current (nA)
            max_depth (int): maximum number of times to run the cell when searching for
                threshold current when precision is not reached

        Returns:
            float: threshold current amplitude (nA)
        """
        # pylint: disable=undefined-loop-variable, too-many-arguments
        step_currents = np.linspace(lower_bound, upper_bound, num=self.short_steps)

        if len(step_currents) == 0:
            return None

        for step_current in step_currents:
            spike_detected = self.detect_spike(
                cell_model,
                param_values,
                sim=sim,
                holdi=holdi,
                step_current=step_current,
                short=True,
            )

            if spike_detected:
                upper_bound = step_current
                break

        # if upper bound didn't have spike with short stimulus
        # check if there is one with longer stimulus
        if not spike_detected:
            spike_detected = self.detect_spike(
                cell_model,
                param_values,
                sim=sim,
                holdi=holdi,
                step_current=step_current,
                short=False,
            )

            if spike_detected:
                upper_bound = step_current
            else:
                return None

        depth = 0
        while depth < max_depth and abs(upper_bound - lower_bound) >= precision:
            middle_bound = upper_bound - abs(upper_bound - lower_bound) / 2
            spike_detected = self.detect_spike(
                cell_model,
                param_values,
                sim=sim,
                holdi=holdi,
                step_current=middle_bound,
                short=False,
            )

            if spike_detected:
                upper_bound = middle_bound
            else:
                lower_bound = middle_bound
            depth += 1

        threshold_current = upper_bound

        return threshold_current


class StepProtocol(ephys.protocols.SweepProtocol, ProtocolMixin):
    """Protocol consisting of step and holding current.

    Attributes:
        name (str): name of this object
        stimuli (list of Stimuli): List of all Stimulus objects used in protocol
        recordings (list of Recordings): Recording objects used in the protocol
        cvode_active (bool): whether to use variable time step
        step_stimuli (list of Stimuli): List of step Stimulus objects used in protocol
        holding_stimulus (Stimulus): Holding Stimulus
        stochkv_det (bool): set if stochastic or deterministic
    """

    def __init__(
        self,
        name=None,
        step_stimuli=None,
        holding_stimulus=None,
        recordings=None,
        cvode_active=None,
        stochkv_det=None,
    ):
        """Constructor.

        Args:
            name (str): name of this object
            step_stimuli (list of Stimuli): List of Stimulus objects used in protocol
            holding_stimulus (Stimulus): Holding Stimulus
            recordings (list of Recordings): Recording objects used in the
                protocol
            cvode_active (bool): whether to use variable time step
            stochkv_det (bool): set if stochastic or deterministic
        """
        super(StepProtocol, self).__init__(
            name,
            stimuli=step_stimuli + [holding_stimulus]
            if holding_stimulus is not None
            else step_stimuli,
            recordings=recordings,
            cvode_active=cvode_active,
        )

        self.step_stimuli = step_stimuli
        # this can be used through inheritance
        self.holding_stimulus = holding_stimulus
        self.stochkv_det = stochkv_det

    def instantiate(self, sim=None, icell=None):
        """Instantiate.

        Args:
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            icell (neuron cell): cell instantiation in simulator
        """
        for stimulus in self.stimuli:
            stimulus.instantiate(sim=sim, icell=icell)

        for recording in self.recordings:
            try:
                recording.instantiate(sim=sim, icell=icell)
            except ephys.locations.EPhysLocInstantiateException as e:
                logger.debug(
                    "SweepProtocol: Instantiating recording generated location "
                    "exception: %s, will return empty response for this recording",
                    e,
                )

    def run(self, cell_model, param_values, sim=None, isolate=None, timeout=None):
        """Run protocol.

        Args:
            cell_model (bluepyopt.ephys.models.CellModel): the cell model
            param_values (dict): optimized parameters
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            isolate (bool): whether to isolate the run in a process with a timeout
                to avoid bad cells running for too long
            timeout (float): maximum real time (s) the cell is allowed to run when isolated

        Returns:
            dict containing the responses for the step protocol
        """
        responses = {}

        cvode_active_copy = self.cvode_active
        if self.stochkv_det is not None and not self.stochkv_det:
            for mechanism in cell_model.mechanisms:
                if "Stoch" in mechanism.prefix:
                    mechanism.deterministic = False
            self.cvode_active = False

        responses.update(
            super(StepProtocol, self).run(
                cell_model, param_values, sim=sim, isolate=isolate, timeout=timeout
            )
        )

        if self.stochkv_det is not None and not self.stochkv_det:
            for mechanism in cell_model.mechanisms:
                if "Stoch" in mechanism.prefix:
                    mechanism.deterministic = True
            self.cvode_active = cvode_active_copy

        return responses

    def generate_current(self, threshold_current=None, holding_current=None, dt=0.1):
        """Return current time series.

        Args:
            threshold_current (float): the threshold current (nA)
            holding_current (float): the holding current (nA)
            dt (float): timestep of the generated currents (ms)

        Returns:
            dict containing the generated current
        """
        # pylint: disable=unused-argument
        holding_current = 0.0
        if self.holding_stimulus is not None:
            holding_current = self.holding_stimulus.step_amplitude
        total_duration = self.step_stimuli[-1].total_duration

        t = np.arange(0.0, total_duration, dt)
        current = np.full(t.shape, holding_current, dtype="float64")

        for stimuli in self.step_stimuli:
            ton = stimuli.step_delay
            ton_idx = int(ton / dt)

            toff = stimuli.step_delay + stimuli.step_duration
            toff_idx = int(toff / dt)

            current[ton_idx:toff_idx] += stimuli.step_amplitude

        return {self.curr_output_key(): {"time": t, "current": current}}

    @property
    def stim_start(self):
        """Time stimulus starts.

        Returns:
            the time at which the stimulus starts (ms)
        """
        return self.step_stimuli[0].step_delay

    @property
    def stim_duration(self):
        """Time stimulus duration.

        Returns:
            the duration of the stimulus (ms)
        """
        return (
            self.step_stimuli[-1].step_delay
            + self.step_stimuli[-1].step_duration
            - self.step_stimuli[0].step_delay
        )

    @property
    def stim_end(self):
        """Time stimulus ends.

        Returns:
            the time at which the stimulus ends (ms)
        """
        return self.step_stimuli[-1].step_delay + self.step_stimuli[-1].step_duration

    @property
    def stim_last_start(self):
        """Time stimulus last start.

        Returns:
            the time at which the last step stimulus in the list starts (ms)
        """
        return self.step_stimuli[-1].step_delay

    @property
    def step_amplitude(self):
        """Stimuli mean amplitude.

        Returns:
            the mean amplitude of the step stimuli (nA)
        """
        amplitudes = [step_stim.step_amplitude for step_stim in self.step_stimuli]

        if None in amplitudes:
            return None
        else:
            return np.mean(amplitudes)


class StepThresholdProtocol(StepProtocol, ProtocolMixin):
    """Step protocol based on threshold.

    Attributes:
        name (str): name of this object
        stimuli (list of Stimuli): List of all Stimulus objects used in protocol
        recordings (list of Recordings): Recording objects used in the protocol
        cvode_active (bool): whether to use variable time step
        step_stimuli (list of Stimuli): List of step Stimulus objects used in protocol
        holding_stimulus (Stimulus): Holding Stimulus
        stochkv_det (bool): set if stochastic or deterministic
        thresh_perc (float): percentage of the threshold current
            at which to set the step amplitudes
    """

    def __init__(
        self,
        name,
        thresh_perc=None,
        step_stimuli=None,
        holding_stimulus=None,
        recordings=None,
        cvode_active=None,
        stochkv_det=None,
    ):
        """Constructor.

        Args:
            name (str): name of this object
            thresh_perc (float): percentage of the threshold current
                at which to set the step amplitudes
            step_stimuli (list of Stimuli): List of Stimulus objects used in protocol
            holding_stimulus (Stimulus): Holding Stimulus
            recordings (list of Recordings): Recording objects used in the
                protocol
            cvode_active (bool): whether to use variable time step
            stochkv_det (bool): set if stochastic or deterministic
        """
        super(StepThresholdProtocol, self).__init__(
            name,
            step_stimuli=step_stimuli,
            holding_stimulus=holding_stimulus,
            recordings=recordings,
            cvode_active=cvode_active,
            stochkv_det=stochkv_det,
        )

        self.thresh_perc = thresh_perc

    def run(self, cell_model, param_values, sim=None, isolate=None, timeout=None):
        """Run protocol.

        Args:
            cell_model (bluepyopt.ephys.models.CellModel): the cell model
            param_values (dict): optimized parameters
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            isolate (bool): whether to isolate the run in a process with a timeout
                to avoid bad cells running for too long
            timeout (float): maximum real time (s) the cell is allowed to run when isolated

        Raises:
            Exception: if the threshold_current is not set to the cell model

        Returns:
            dict containing the responses for the step protocol
        """
        # pylint: disable=unused-argument
        responses = {}
        if not hasattr(cell_model, "threshold_current"):
            raise Exception(
                "StepThresholdProtocol: running on cell_model "
                f"that doesnt have threshold current value set: {cell_model}"
            )

        for step_stim in self.step_stimuli:
            step_stim.step_amplitude = cell_model.threshold_current * (
                float(self.thresh_perc) / 100.0
            )

        self.holding_stimulus.step_amplitude = cell_model.holding_current

        responses.update(
            super(StepThresholdProtocol, self).run(
                cell_model, param_values, sim=sim, isolate=isolate, timeout=timeout
            )
        )

        return responses

    def generate_current(self, threshold_current, holding_current, dt=0.1):
        """Return current time series.

        Args:
            threshold_current (float): the threshold current (nA)
            holding_current (float): the holding current (nA)
            dt (float): timestep of the generated currents (ms)

        Returns:
            dict containing the generated current
        """
        # pylint: disable=signature-differs
        total_duration = self.step_stimuli[-1].total_duration

        t = np.arange(0.0, total_duration, dt)
        current = np.full(t.shape, holding_current, dtype="float64")

        for stimuli in self.step_stimuli:
            ton = stimuli.step_delay
            ton_idx = int(ton / dt)

            toff = stimuli.step_delay + stimuli.step_duration
            toff_idx = int(toff / dt)

            current[ton_idx:toff_idx] += threshold_current * (
                float(self.thresh_perc) / 100.0
            )

        return {self.curr_output_key(): {"time": t, "current": current}}


class RampProtocol(ephys.protocols.SweepProtocol, ProtocolMixin):
    """Protocol consisting of ramp and holding current.

    Attributes:
        name (str): name of this object
        stimuli (list of Stimuli): List of all Stimulus objects used in protocol
        recordings (list of Recordings): Recording objects used in the protocol
        cvode_active (bool): whether to use variable time step
        ramp_stimulus (Stimulus): ramp Stimulus
        holding_stimulus (Stimulus): Holding Stimulus
    """

    def __init__(
        self,
        name=None,
        ramp_stimulus=None,
        holding_stimulus=None,
        recordings=None,
        cvode_active=None,
    ):
        """Constructor.

        Args:
            name (str): name of this object
            ramp_stimulus (Stimulus): Stimulus objects used in protocol
            holding_stimulus (Stimulus): Holding Stimulus
            recordings (list of Recordings): Recording objects used in the
                protocol
            cvode_active (bool): whether to use variable time step
        """
        super(RampProtocol, self).__init__(
            name,
            stimuli=[ramp_stimulus, holding_stimulus]
            if holding_stimulus is not None
            else [ramp_stimulus],
            recordings=recordings,
            cvode_active=cvode_active,
        )

        self.ramp_stimulus = ramp_stimulus
        self.holding_stimulus = holding_stimulus

    def generate_current(self, threshold_current=None, holding_current=None, dt=0.1):
        """Return current time series.

        Args:
            threshold_current (float): the threshold current (nA)
            holding_current (float): the holding current (nA)
            dt (float): timestep of the generated currents (ms)

        Returns:
            dict containing the generated current
        """
        # pylint: disable=unused-argument
        holding_current = 0.0
        if self.holding_stimulus is not None:
            holding_current = self.holding_stimulus.step_amplitude
        t = np.arange(0.0, self.ramp_stimulus.total_duration, dt)
        current = np.full(t.shape, holding_current, dtype="float64")

        ton_idx = int(self.step_delay / dt)
        toff_idx = int((self.step_delay + self.step_duration) / dt)

        current[ton_idx:toff_idx] += np.linspace(
            self.ramp_stimulus.ramp_amplitude_start,
            self.ramp_stimulus.ramp_amplitude_end,
            toff_idx - ton_idx + 1,
        )[:-1]

        return {self.curr_output_key(): {"time": t, "current": current}}

    @property
    def step_delay(self):
        """Time stimulus delay.

        Returns:
            time at which the ramp starts (ms)
        """
        return self.ramp_stimulus.ramp_delay

    @property
    def step_duration(self):
        """Time stimulus duration.

        Returns:
            duration of the ramp stimulus (ms)
        """
        return self.ramp_stimulus.ramp_duration


class RampThresholdProtocol(RampProtocol, ProtocolMixin):
    """Step protocol based on threshold.

    Attributes:
        name (str): name of this object
        stimuli (list of Stimuli): List of all Stimulus objects used in protocol
        recordings (list of Recordings): Recording objects used in the protocol
        cvode_active (bool): whether to use variable time step
        ramp_stimulus (Stimulus): ramp Stimulus
        holding_stimulus (Stimulus): Holding Stimulus
        thresh_perc_start (float): percentage of the threshold current
            at which to set the start of the ramp amplitude
        thresh_perc_end (float): percentage of the threshold current
            at which to set the end of the ramp amplitude
    """

    def __init__(
        self,
        name,
        thresh_perc_start=None,
        thresh_perc_end=None,
        ramp_stimulus=None,
        holding_stimulus=None,
        recordings=None,
        cvode_active=None,
    ):
        """Constructor.

        Args:
           name (str): name of this object
           thresh_perc_start (float): percentage of the threshold current
               at which to set the start of the ramp amplitude
           thresh_perc_end (float): percentage of the threshold current
               at which to set the end of the ramp amplitude
           ramp_stimulus (Stimulus): Stimulus objects used in protocol
           holding_stimulus (Stimulus): Holding Stimulus
           recordings (list of Recordings): Recording objects used in the
               protocol
           cvode_active (bool): whether to use variable time step
        """
        super(RampThresholdProtocol, self).__init__(
            name,
            ramp_stimulus=ramp_stimulus,
            holding_stimulus=holding_stimulus,
            recordings=recordings,
            cvode_active=cvode_active,
        )

        self.thresh_perc_start = thresh_perc_start
        self.thresh_perc_end = thresh_perc_end

    def run(self, cell_model, param_values, sim=None, isolate=None, timeout=None):
        """Run protocol.

        Args:
            cell_model (bluepyopt.ephys.models.CellModel): the cell model
            param_values (dict): optimized parameters
            sim (bluepyopt.ephys.NrnSimulator): neuron simulator
            isolate (bool): whether to isolate the run in a process with a timeout
                to avoid bad cells running for too long
            timeout (float): maximum real time (s) the cell is allowed to run when isolated

        Raises:
            Exception: if the threshold_current is not set to the cell model

        Returns:
            dict containing the responses for the ramp protocol
        """
        # pylint: disable=unused-argument
        responses = {}
        if not hasattr(cell_model, "threshold_current"):
            raise Exception(
                "RampThresholdProtocol: running on cell_model "
                f"that doesnt have threshold current value set: {cell_model}"
            )

        self.ramp_stimulus.ramp_amplitude_start = cell_model.threshold_current * (
            float(self.thresh_perc_start) / 100
        )
        self.ramp_stimulus.ramp_amplitude_end = cell_model.threshold_current * (
            float(self.thresh_perc_end) / 100
        )

        self.holding_stimulus.step_amplitude = cell_model.holding_current

        responses.update(
            super(RampThresholdProtocol, self).run(
                cell_model, param_values, sim=sim, isolate=isolate, timeout=timeout
            )
        )

        return responses

    def generate_current(self, threshold_current, holding_current, dt=0.1):
        """Return current time series.

        Args:
            threshold_current (float): the threshold current (nA)
            holding_current (float): the holding current (nA)
            dt (float): timestep of the generated currents (ms)

        Returns:
            dict containing the generated current
        """
        # pylint: disable=signature-differs
        t = np.arange(0.0, self.ramp_stimulus.total_duration, dt)
        current = np.full(t.shape, holding_current, dtype="float64")

        ton_idx = int(self.step_delay / dt)
        toff_idx = int((self.step_delay + self.step_duration) / dt)

        amp_start = threshold_current * (float(self.thresh_perc_start) / 100)
        amp_end = threshold_current * (float(self.thresh_perc_end) / 100)
        current[ton_idx:toff_idx] += np.linspace(
            amp_start,
            amp_end,
            toff_idx - ton_idx + 1,
        )[:-1]

        return {self.curr_output_key(): {"time": t, "current": current}}


class SweepProtocolCustom(ephys.protocols.SweepProtocol):
    """SweepProtocol with generate_current method.

    Attributes:
        name (str): name of this object
        stimuli (list of Stimuli): List of all Stimulus objects used in protocol
        recordings (list of Recordings): Recording objects used in the protocol
        cvode_active (bool): whether to use variable time step

    Args of the parent constructor:

    - name (str): name of this object
    - stimuli (list of Stimuli): Stimulus objects used in the protocol
    - recordings (list of Recordings): Recording objects used in the protocol
    - cvode_active (bool): whether to use variable time step
    """

    @staticmethod
    def generate_current(threshold_current, holding_current, dt=0.1):
        """Return an empty dictionary.

        Args:
            threshold_current (float): the threshold current (nA)
            holding_current (float): the holding current (nA)
            dt (float): timestep of the generated currents (ms)

        Returns:
            empty dict
        """
        # pylint: disable=unused-argument
        return {}
