"""Physiology features extraction and representation."""

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

import efel


def extract_physiology_features(
    time, voltage, current_amplitude, stim_start, stim_duration
):
    """Extract voltage_base, input_resistance and decay_time_constant features.

    Args:
        time (list): time corresponding to the voltage data of the trace (ms)
        voltage (list): voltage data of the trace (mV)
        current_amplitude (float): current amplitude of the stimulus (nA)
        stim_start (float): time at which the stimulus begins (ms)
        stim_duration (float): stimulus duration (ms)

    Returns:
        list containing voltage base, input resistance and decay time constant features
    """
    # Prepare the trace data
    trace = {}
    trace["T"] = time
    trace["V"] = voltage
    trace["stim_start"] = [stim_start]
    trace["stim_end"] = [stim_start + stim_duration]

    # Calculate the necessary eFeatures
    efel_results = efel.getFeatureValues(
        [trace],
        [
            "voltage_base",
            "steady_state_voltage_stimend",
            "decay_time_constant_after_stim",
        ],
    )

    voltage_base = efel_results[0]["voltage_base"][0]
    dct = efel_results[0]["decay_time_constant_after_stim"][0]

    trace["decay_start_after_stim"] = efel_results[0]["voltage_base"]
    trace["stimulus_current"] = [current_amplitude]

    efel_results = efel.getFeatureValues([trace], ["ohmic_input_resistance_vb_ssse"])
    input_resistance = efel_results[0]["ohmic_input_resistance_vb_ssse"][0]

    return [voltage_base, input_resistance, dct]


def physiology_features_wrapper(voltage_base, input_resistance, dct):
    """Wraps the extracted features into the dictionary format with names and units.

    Args:
        voltage_base (float): resting membrane potential (mV)
        input_resistance (float): input resistance (MOhm)
        dct (float): membrane time constant (ms)

    Returns:
        list containing dicts with each input feature name, value and unit
    """
    factsheet_info = []
    factsheet_info.append(
        {"name": "resting membrane potential", "value": voltage_base, "unit": "mV"}
    )
    factsheet_info.append(
        {"name": "input resistance", "value": input_resistance, "unit": "MOhm"}
    )
    factsheet_info.append(
        {"name": "membrane time constant", "value": dct, "unit": "ms"}
    )
    return factsheet_info


def physiology_factsheet_info(
    time, voltage, current_amplitude, stim_start, stim_duration
):
    """Provides complete physiology information for the factsheet.

    Args:
        time (list): time corresponding to the voltage data of the trace (ms)
        voltage (list): voltage data of the trace (mV)
        current_amplitude (float): current amplitude of the stimulus (nA)
        stim_start (float): time at which the stimulus begins (ms)
        stim_duration (float): stimulus duration (ms)

    Returns:
        dict containing the physiology data
    """
    voltage_base, input_resistance, dct = extract_physiology_features(
        time, voltage, current_amplitude, stim_start, stim_duration
    )
    factsheet_info = physiology_features_wrapper(voltage_base, input_resistance, dct)
    return {"name": "Physiology", "values": factsheet_info}
