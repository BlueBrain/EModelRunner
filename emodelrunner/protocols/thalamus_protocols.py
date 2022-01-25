"""Ephys protocols for the Thalamus packages."""

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

import warnings
import collections
import copy
import numpy as np
from bluepyopt import ephys

from emodelrunner.protocols.protocols_func import CurrentOutputKeyMixin


class RatSSCxMainProtocol(ephys.protocols.Protocol):
    """Main protocol to fit RatSSCx neuron ephys parameters.

    Pseudo code:
        Find resting membrane potential
        Find input resistance
        If both of these scores are within bounds, run other protocols:
        - Find holding current
        - Find rheobase
        - Run IDRest
        - Possibly run other protocols (based on constructor arguments)
        - Return all the responses
        Otherwise return Rin and RMP protocol responses
    """

    def __init__(
        self,
        name,
        rmp_protocol=None,
        rmp_efeature=None,
        rinhold_protocol_dep=None,
        rinhold_protocol_hyp=None,
        rin_efeature_dep=None,
        rin_efeature_hyp=None,
        thdetect_protocol_dep=None,
        thdetect_protocol_hyp=None,
        other_protocols=None,
        pre_protocols=None,
        fitness_calculator=None,
    ):
        """Constructor."""
        # pylint: disable=too-many-arguments
        super().__init__(name=name)

        self.rmp_protocol = rmp_protocol
        self.rmp_efeature = rmp_efeature

        if rinhold_protocol_dep is not None:
            self.rinhold_protocol_dep = rinhold_protocol_dep
            self.rin_efeature_dep = rin_efeature_dep

        self.rinhold_protocol_hyp = rinhold_protocol_hyp
        self.rin_efeature_hyp = rin_efeature_hyp

        if thdetect_protocol_dep is not None:
            self.thdetect_protocol_dep = thdetect_protocol_dep

        self.thdetect_protocol_hyp = thdetect_protocol_hyp

        self.other_protocols = other_protocols

        self.pre_protocols = pre_protocols

        self.fitness_calculator = fitness_calculator

    def subprotocols(self):
        """Return all the subprotocols contained in this protocol, is recursive."""
        subprotocols = collections.OrderedDict({self.name: self})
        subprotocols.update(self.rmp_protocol.subprotocols())
        if hasattr(self, "rinhold_protocol_dep"):
            subprotocols.update(self.rinhold_protocol_dep.subprotocols())
        subprotocols.update(self.rinhold_protocol_hyp.subprotocols())
        if hasattr(self, "thdetect_protocol_dep"):
            subprotocols.update(self.thdetect_protocol_dep.subprotocols())
        subprotocols.update(self.thdetect_protocol_hyp.subprotocols())
        for other_protocol in self.other_protocols:
            subprotocols.update(other_protocol.subprotocols())
        for pre_protocol in self.pre_protocols:
            subprotocols.update(pre_protocol.subprotocols())

        return subprotocols

    @property
    def rin_efeature_dep(self):
        """Get in_efeature."""
        return self.rinhold_protocol_dep.rin_efeature_dep

    @rin_efeature_dep.setter
    def rin_efeature_dep(self, value):
        """Set rin_efeature."""
        self.rinhold_protocol_dep.rin_efeature_dep = value

    @property
    def rin_efeature_hyp(self):
        """Get in_efeature."""
        return self.rinhold_protocol_hyp.rin_efeature_hyp

    @rin_efeature_hyp.setter
    def rin_efeature_hyp(self, value):
        """Set rin_efeature."""
        self.rinhold_protocol_hyp.rin_efeature_hyp = value

    def run(self, cell_model, param_values, sim=None, isolate=None):
        """Run protocol."""
        # pylint: disable=unused-argument
        responses = collections.OrderedDict()

        cell_model.freeze(param_values)

        # Find resting membrane potential
        rmp_response = self.rmp_protocol.run(cell_model, {}, sim=sim)
        responses.update(rmp_response)
        rmp = self.rmp_efeature.calculate_feature(rmp_response)

        # Find Rin and holding current
        if hasattr(self, "rinhold_protocol_dep"):
            rinhold_response_dep = self.rinhold_protocol_dep.run(
                cell_model, {}, sim=sim, rmp=rmp
            )
            holding_current_dep = cell_model.holding_current_dep

            rin_dep = self.rin_efeature_dep.calculate_feature(rinhold_response_dep)
            responses.update(rinhold_response_dep)

        rinhold_response_hyp = self.rinhold_protocol_hyp.run(
            cell_model, {}, sim=sim, rmp=rmp
        )

        if rinhold_response_hyp is not None:
            rin_hyp = self.rin_efeature_hyp.calculate_feature(rinhold_response_hyp)

            responses.update(rinhold_response_hyp)

            if hasattr(self, "thdetect_protocol_dep"):
                responses.update(
                    self.thdetect_protocol_dep.run(
                        cell_model,
                        {},
                        sim=sim,
                        holdi=holding_current_dep,
                        rmp=rmp,
                        rin=rin_dep,
                    )
                )

            responses.update(
                self.thdetect_protocol_hyp.run(
                    cell_model,
                    {},
                    sim=sim,
                    holdi=cell_model.holding_current_hyp,
                    rmp=rmp,
                    rin=rin_hyp,
                )
            )

            if cell_model.threshold_current_hyp is not None:
                self._run_pre_protocols(cell_model, sim, responses)
                self._run_other_protocols(cell_model, sim, responses)

        cell_model.unfreeze(param_values.keys())

        return responses

    def _run_pre_protocols(self, cell_model, sim, responses):
        """Runs the pre_protocols and updates responses dict."""
        for pre_protocol in self.pre_protocols:
            response = pre_protocol.run(cell_model, {}, sim=sim)
            responses.update(response)

    def _run_other_protocols(self, cell_model, sim, responses):
        """Runs the other_protocols and updates responses dict."""
        for other_protocol in self.other_protocols:
            response = other_protocol.run(cell_model, {}, sim=sim)
            responses.update(response)

    def generate_current(
        self, thres_i_hyp, thres_i_dep, holding_i_hyp, holding_i_dep, dt
    ):
        """Generate current for all protocols except rin and threshold detection.

        Args:
            thres_i_hyp (float): hyperpolarization threshold current (nA)
            thres_i_dep (float): depolarization threshold current (nA)
            holding_i_hyp (float): hyperpolarization holding current (nA)
            holding_i_dep (float): depolarization holding current (nA)
            dt (float): timestep of the generated currents (ms)

        Returns:
            dict containing the generated currents
        """
        currents = {}

        # rmp is step protocol
        currents.update(
            self.rmp_protocol.generate_current(
                threshold_current=thres_i_dep,
                holding_current=holding_i_dep,
                dt=dt,
            )
        )

        for pre_protocol in self.pre_protocols:
            if "_hyp" in pre_protocol.name:
                pre_prot_threshold_current = thres_i_hyp
                pre_prot_holding_current = holding_i_hyp
            else:
                pre_prot_threshold_current = thres_i_dep
                pre_prot_holding_current = holding_i_dep
            currents.update(
                pre_protocol.generate_current(
                    threshold_current=pre_prot_threshold_current,
                    holding_current=pre_prot_holding_current,
                    dt=dt,
                )
            )

        for other_protocol in self.other_protocols:
            if "_hyp" in other_protocol.name:
                other_prot_threshold_current = thres_i_hyp
                other_prot_holding_current = holding_i_hyp
            else:
                other_prot_threshold_current = thres_i_dep
                other_prot_holding_current = holding_i_dep
            currents.update(
                other_protocol.generate_current(
                    threshold_current=other_prot_threshold_current,
                    holding_current=other_prot_holding_current,
                    dt=dt,
                )
            )

        return currents


class RatSSCxRinHoldcurrentProtocol(ephys.protocols.Protocol):
    """IDRest protocol to fit RatSSCx neuron ephys parameters."""

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
        """Constructor."""
        # pylint: disable=too-many-arguments
        super().__init__(name=name)
        self.rin_protocol_template = rin_protocol_template
        self.voltagebase_efeature = voltagebase_efeature
        self.holdi_estimate_multiplier = holdi_estimate_multiplier
        self.holdi_precision = holdi_precision
        self.holdi_max_depth = holdi_max_depth

        self.rin_efeature_dep = None
        self.rin_efeature_hyp = None

        self.prefix = "" if prefix is None else prefix + "."
        # This will be set after the run()
        self.rin_protocol = None

    def run(self, cell_model, param_values, sim, rmp=None):
        """Run protocol."""
        responses = collections.OrderedDict()

        # Calculate Rin without holding current
        if "dep" in self.name:
            rin_noholding_protocol = self.create_rin_protocol_dep(holdi=0)
            rin_noholding_response = rin_noholding_protocol.run(
                cell_model, param_values, sim=sim
            )
            rin_noholding = self.rin_efeature_dep.calculate_feature(
                rin_noholding_response
            )

        elif "hyp" in self.name:
            rin_noholding_protocol = self.create_rin_protocol_hyp(holdi=0)
            rin_noholding_response = rin_noholding_protocol.run(
                cell_model, param_values, sim=sim
            )
            rin_noholding = self.rin_efeature_hyp.calculate_feature(
                rin_noholding_response
            )

        print(f"Rin without holdi is {rin_noholding}")

        print(f"Searching holdi for vhold = {self.voltagebase_efeature.exp_mean}")
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
        if "dep" in self.name:
            self.rin_protocol = self.create_rin_protocol_dep(holdi=holdi)
        elif "hyp" in self.name:
            self.rin_protocol = self.create_rin_protocol_hyp(holdi=holdi)

        # Return response
        responses = self.rin_protocol.run(cell_model, param_values, sim)

        if "dep" in self.name:
            responses[self.prefix + "bpo_holding_current_dep"] = holdi
            cell_model.holding_current_dep = holdi

        elif "hyp" in self.name:
            responses[self.prefix + "bpo_holding_current_hyp"] = holdi
            cell_model.holding_current_hyp = holdi

        return responses

    def subprotocols(self):
        """Return subprotocols."""
        subprotocols = collections.OrderedDict({self.name: self})

        subprotocols.update(
            {self.rin_protocol_template.name: self.rin_protocol_template}
        )

        return subprotocols

    def create_rin_protocol_dep(self, holdi=None):
        """Create Rin_dep protocol."""
        return self._create_rin_protocol("Rin_dep", holdi)

    def create_rin_protocol_hyp(self, holdi=None):
        """Create rin_hyp protocol."""
        return self._create_rin_protocol("Rin_hyp", holdi)

    def _create_rin_protocol(self, protocol_name, holdi):
        """Create rin protocol from self.rin_protocol_template."""
        rin_protocol = copy.deepcopy(self.rin_protocol_template)
        rin_protocol.name = protocol_name
        for recording in rin_protocol.recordings:
            recording.name = recording.name.replace(
                self.rin_protocol_template.name, rin_protocol.name
            )

        rin_protocol.holding_stimulus.step_amplitude = holdi
        return rin_protocol

    def search_holdi(
        self, cell_model, param_values, sim, holding_voltage, rin_noholding, rmp
    ):
        """Find the holding current to hold cell at holding_voltage."""
        holdi_estimate = float(holding_voltage - rmp) / rin_noholding
        print(
            f"Holdi estimate is {holdi_estimate} with target vhold {holding_voltage}"
            f", rmp {rmp}, Rin {rin_noholding}"
        )

        return self.binsearch_holdi(
            holding_voltage,
            cell_model,
            param_values,
            sim,
            upper_bound=0.22,
            lower_bound=self.holdi_estimate_multiplier * holdi_estimate,
            precision=self.holdi_precision,
            max_depth=self.holdi_max_depth,
        )

    def binsearch_holdi(
        self,
        holding_voltage,
        cell_model,
        param_values,
        sim=None,
        lower_bound=None,
        upper_bound=None,
        precision=None,
        max_depth=None,
        depth=1,
    ):
        """Do binary search to find holding current."""
        # pylint: disable=too-many-arguments
        middle_bound = upper_bound - abs(upper_bound - lower_bound) / 2

        if depth > max_depth:
            print(
                f"Search holdi reached max depth, returning with ihold {middle_bound}"
            )
            return middle_bound
        else:
            middle_voltage = self.voltage_base(
                middle_bound, cell_model, param_values, sim=sim
            )

            if middle_voltage is None:
                warnings.warn("Holdi current search failed")
                return None

            if abs(middle_voltage - holding_voltage) < precision:
                print(f"Holdi search reached precision of {precision}")
                return middle_bound

            elif middle_voltage > holding_voltage:
                return self.binsearch_holdi(
                    holding_voltage,
                    cell_model,
                    param_values,
                    sim=sim,
                    lower_bound=lower_bound,
                    upper_bound=middle_bound,
                    precision=precision,
                    max_depth=max_depth,
                    depth=depth + 1,
                )
            elif middle_voltage < holding_voltage:
                return self.binsearch_holdi(
                    holding_voltage,
                    cell_model,
                    param_values,
                    sim=sim,
                    lower_bound=middle_bound,
                    upper_bound=upper_bound,
                    precision=precision,
                    max_depth=max_depth,
                    depth=depth + 1,
                )
            else:
                return None

    def voltage_base(self, current, cell_model, param_values, sim=None):
        """Calculate voltage base for certain stimulus current."""
        if "dep" in self.name:
            protocol = self.create_rin_protocol_dep(holdi=current)

            response = protocol.run(cell_model, param_values, sim=sim)

            feature = ephys.efeatures.eFELFeature(
                name="Holding_dep.voltage_base",
                efel_feature_name="voltage_base",
                recording_names={"": self.prefix + "Rin_dep.soma.v"},
                stim_start=protocol.step_delay,
                stim_end=protocol.step_delay + protocol.step_duration,
                exp_mean=0,
                exp_std=0.1,
            )

            voltage_base = feature.calculate_feature(response)

        elif "hyp" in self.name:
            protocol = self.create_rin_protocol_hyp(holdi=current)

            response = protocol.run(cell_model, param_values, sim=sim)

            feature = ephys.efeatures.eFELFeature(
                name="Holding_hyp.voltage_base",
                efel_feature_name="voltage_base",
                recording_names={"": self.prefix + "Rin_hyp.soma.v"},
                stim_start=protocol.step_delay,
                stim_end=protocol.step_delay + protocol.step_duration,
                exp_mean=0,
                exp_std=0.1,
            )

            voltage_base = feature.calculate_feature(response)
        return voltage_base


class RatSSCxThresholdDetectionProtocol(ephys.protocols.Protocol):
    """IDRest protocol to fit RatSSCx neuron ephys parameters."""

    def __init__(
        self,
        name,
        step_protocol_template=None,
        max_threshold_voltage=None,
        holding_voltage=None,
        prefix=None,
    ):
        """Constructor."""
        super().__init__(name=name)

        self.step_protocol_template = step_protocol_template

        if max_threshold_voltage is None:
            if "dep" in self.name:
                max_threshold_voltage = -40
            elif "hyp" in self.name:
                max_threshold_voltage = -50

        self.max_threshold_voltage = max_threshold_voltage

        self.short_perc = 0.1
        self.short_steps = 5
        self.holding_voltage = holding_voltage

        self.prefix = "" if prefix is None else prefix + "."

    def subprotocols(self):
        """Return subprotocols."""
        subprotocols = collections.OrderedDict({self.name: self})

        subprotocols.update(self.step_protocol_template.subprotocols())

        return subprotocols

    def run(self, cell_model, param_values, sim, holdi, rin, rmp):
        """Run protocol."""
        # pylint: disable=unused-argument
        responses = collections.OrderedDict()

        # Calculate max threshold current
        max_threshold_current = self.search_max_threshold_current(rin=rin)

        # Calculate spike threshold
        threshold_current = self.search_spike_threshold(
            cell_model,
            {},
            holdi=holdi,
            lower_bound=0,
            upper_bound=max_threshold_current,
            sim=sim,
        )

        if "dep" in self.name:
            cell_model.threshold_current_dep = threshold_current
            responses[self.prefix + "bpo_threshold_current_dep"] = threshold_current

        if "hyp" in self.name:
            cell_model.threshold_current_hyp = threshold_current
            responses[self.prefix + "bpo_threshold_current_hyp"] = threshold_current

        return responses

    def search_max_threshold_current(self, rin=None):
        """Find the current necessary to get to max_threshold_voltage."""
        max_threshold_current = (
            float(self.max_threshold_voltage - self.holding_voltage) / rin
        )

        print(
            f"Max threshold current from vhold {self.holding_voltage}: {max_threshold_current}"
        )

        return max_threshold_current

    def create_step_protocol(self, holdi=0.0, step_current=0.0):
        """Create threshold protocol."""
        threshold_protocol = copy.deepcopy(self.step_protocol_template)

        if "dep" in self.name:
            threshold_protocol.name = "ThresholdDetection_dep"
        elif "hyp" in self.name:
            threshold_protocol.name = "ThresholdDetection_hyp"

        for recording in threshold_protocol.recordings:
            recording.name = recording.name.replace(
                self.step_protocol_template.name, threshold_protocol.name
            )

        if threshold_protocol.holding_stimulus is not None:
            threshold_protocol.holding_stimulus.step_amplitude = holdi
        threshold_protocol.step_stimulus.step_amplitude = step_current

        return threshold_protocol

    def create_short_threshold_protocol(self, holdi=None, step_current=None):
        """Create short threshold protocol."""
        short_protocol = self.create_step_protocol(
            holdi=holdi, step_current=step_current
        )
        origin_step_duration = short_protocol.step_stimulus.step_duration
        origin_step_delay = short_protocol.step_stimulus.step_delay

        short_step_duration = origin_step_duration * self.short_perc
        short_total_duration = origin_step_delay + short_step_duration

        short_protocol.step_stimulus.step_duration = short_step_duration
        short_protocol.step_stimulus.total_duration = short_total_duration

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
        """Detect if spike is present at current level."""
        # Only run short pulse if percentage set smaller than 100%
        if short and self.short_perc < 1.0:
            protocol = self.create_short_threshold_protocol(
                holdi=holdi, step_current=step_current
            )
        else:
            protocol = self.create_step_protocol(holdi=holdi, step_current=step_current)

        response = protocol.run(cell_model, param_values, sim=sim)
        print(protocol)
        if "dep" in self.name:
            feature = ephys.efeatures.eFELFeature(
                name="ThresholdDetection_dep.Spikecount",
                efel_feature_name="Spikecount_stimint",
                recording_names={"": self.prefix + "ThresholdDetection_dep.soma.v"},
                stim_start=protocol.step_delay,
                stim_end=protocol.step_delay + protocol.step_duration,
                exp_mean=1,
                exp_std=0.1,
            )

        elif "hyp" in self.name:
            feature = ephys.efeatures.eFELFeature(
                name="ThresholdDetection_hyp.Spikecount",
                efel_feature_name="Spikecount_stimint",
                recording_names={"": self.prefix + "ThresholdDetection_hyp.soma.v"},
                stim_start=protocol.step_delay,
                stim_end=protocol.step_delay + protocol.step_duration,
                exp_mean=1,
                exp_std=0.1,
            )

        spike_count = feature.calculate_feature(response)
        print(f"{spike_count} spikes with I = {step_current}")
        return spike_count >= 1

    def binsearch_spike_threshold(
        self,
        cell_model,
        param_values,
        sim=None,
        holdi=None,
        lower_bound=None,
        upper_bound=None,
        precision=0.01,
        max_depth=5,
        depth=1,
    ):
        """Do binary search to find spike threshold.

        Assumption is that lower_bound has no spike, upper_bound has.
        """
        # pylint: disable=too-many-arguments
        if depth > max_depth or abs(upper_bound - lower_bound) < precision:
            return upper_bound
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
            return self.binsearch_spike_threshold(
                cell_model,
                param_values,
                sim=sim,
                holdi=holdi,
                lower_bound=lower_bound,
                upper_bound=middle_bound,
                depth=depth + 1,
            )
        else:
            return self.binsearch_spike_threshold(
                cell_model,
                param_values,
                sim=sim,
                holdi=holdi,
                lower_bound=middle_bound,
                upper_bound=upper_bound,
                depth=depth + 1,
            )

    def search_spike_threshold(
        self,
        cell_model,
        param_values,
        sim=None,
        holdi=None,
        lower_bound=None,
        upper_bound=None,
    ):
        """Find the current step spiking threshold."""
        step_currents = np.linspace(lower_bound, upper_bound, num=self.short_steps)

        if len(step_currents) == 0:
            return None

        for step_current in step_currents:
            latest_step_current = step_current
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
                step_current=latest_step_current,
                short=False,
            )

            if spike_detected:
                upper_bound = latest_step_current
            else:
                return None

        threshold_current = self.binsearch_spike_threshold(
            cell_model,
            {},
            sim=sim,
            holdi=holdi,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )
        print(f"Threshold current from {holdi} is {threshold_current}")
        return threshold_current


class StepProtocolCustom(ephys.protocols.StepProtocol, CurrentOutputKeyMixin):
    """Step protocol with custom options to turn stochkv_det on or off."""

    def __init__(
        self,
        name=None,
        step_stimulus=None,
        holding_stimulus=None,
        recordings=None,
        cvode_active=None,
        stochkv_det=None,
    ):
        """Constructor."""
        super().__init__(
            name,
            step_stimulus=step_stimulus,
            holding_stimulus=holding_stimulus,
            recordings=recordings,
            cvode_active=cvode_active,
        )

        self.stochkv_det = stochkv_det

    def run(self, cell_model, param_values, sim=None, isolate=None, timeout=None):
        """Run protocol."""
        responses = {}

        if self.stochkv_det is not None and not self.stochkv_det:
            for mechanism in cell_model.mechanisms:
                if "Stoch" in mechanism.prefix:
                    mechanism.deterministic = False
            self.cvode_active = False

        responses.update(
            super().run(
                cell_model, param_values, sim=sim, isolate=isolate, timeout=timeout
            )
        )

        if self.stochkv_det is not None and not self.stochkv_det:
            for mechanism in cell_model.mechanisms:
                if "Stoch" in mechanism.prefix:
                    mechanism.deterministic = True
            self.cvode_active = True

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
        total_duration = self.step_stimulus.total_duration

        t = np.arange(0.0, total_duration, dt)
        current = np.full(t.shape, holding_current, dtype="float64")

        ton = self.step_stimulus.step_delay
        ton_idx = int(ton / dt)

        toff = self.step_stimulus.step_delay + self.step_stimulus.step_duration
        toff_idx = int(toff / dt)

        current[ton_idx:toff_idx] += self.step_stimulus.step_amplitude

        return {self.curr_output_key(): {"time": t, "current": current}}

    @property
    def stim_start(self):
        """Time stimulus starts.

        Returns:
            the time at which the stimulus starts (ms)
        """
        return self.step_stimulus.step_delay

    @property
    def stim_end(self):
        """Time stimulus ends.

        Returns:
            the time at which the stimulus ends (ms)
        """
        return self.step_stimulus.step_delay + self.step_stimulus.step_duration

    @property
    def step_amplitude(self):
        """Stimuli amplitude.

        Returns:
            the amplitude of the step stimuli (nA)
        """
        return self.step_stimulus.step_amplitude


class StepThresholdProtocol(StepProtocolCustom):
    """Step protocol based on threshold."""

    def __init__(
        self,
        name,
        thresh_perc=None,
        step_stimulus=None,
        holding_stimulus=None,
        recordings=None,
        cvode_active=None,
        stochkv_det=None,
    ):
        """Constructor."""
        super().__init__(
            name,
            step_stimulus=step_stimulus,
            holding_stimulus=holding_stimulus,
            recordings=recordings,
            cvode_active=cvode_active,
        )

        self.thresh_perc = thresh_perc
        self.stochkv_det = stochkv_det

    def run(self, cell_model, param_values, sim=None, isolate=None, timeout=None):
        """Run protocol."""
        print(f"Running protocol {self.name}")
        responses = {}
        if not hasattr(cell_model, "threshold_current_hyp"):
            raise Exception(
                f"StepThresholdProtocol: running on cell_model "
                f"that doesnt have threshold current value set: {str(cell_model)}",
            )

        if "hyp" in self.name:
            self.holding_stimulus.step_amplitude = cell_model.holding_current_hyp

            self.step_stimulus.step_amplitude = cell_model.threshold_current_hyp * (
                float(self.thresh_perc) / 100
            )

        else:
            self.holding_stimulus.step_amplitude = cell_model.holding_current_dep

            self.step_stimulus.step_amplitude = cell_model.threshold_current_dep * (
                float(self.thresh_perc) / 100
            )

        if self.stochkv_det is not None and not self.stochkv_det:
            for mechanism in cell_model.mechanisms:
                if "Stoch" in mechanism.prefix:
                    mechanism.deterministic = False
            self.cvode_active = False

        responses.update(
            super().run(
                cell_model, param_values, sim=sim, isolate=isolate, timeout=timeout
            )
        )

        if self.stochkv_det is not None and not self.stochkv_det:
            for mechanism in cell_model.mechanisms:
                if "Stoch" in mechanism.prefix:
                    mechanism.deterministic = True
            self.cvode_active = True

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
        total_duration = self.step_stimulus.total_duration

        t = np.arange(0.0, total_duration, dt)
        current = np.full(t.shape, holding_current, dtype="float64")

        ton = self.step_stimulus.step_delay
        ton_idx = int(ton / dt)

        toff = self.step_stimulus.step_delay + self.step_stimulus.step_duration
        toff_idx = int(toff / dt)

        if threshold_current is not None:
            current[ton_idx:toff_idx] += threshold_current * (
                float(self.thresh_perc) / 100.0
            )

        return {self.curr_output_key(): {"time": t, "current": current}}
