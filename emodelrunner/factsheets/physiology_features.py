"""Physiology features extraction and representation."""

import efel


def extract_physiology_features(
    time, voltage, current_amplitude, stim_start, stim_duration
):
    """Extract voltage_base, input_resistance and decay_time_constant features."""
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
    """Wraps the extracted features into the dictionary format with names and units."""
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
    """Provides complete physiology information for the factsheet."""
    voltage_base, input_resistance, dct = extract_physiology_features(
        time, voltage, current_amplitude, stim_start, stim_duration
    )
    factsheet_info = physiology_features_wrapper(voltage_base, input_resistance, dct)
    return {"name": "Physiology", "values": factsheet_info}
