"""Analysis tools for synapse plasticity."""

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

import h5py
import numpy as np


def get_epsp_vector(t, v, spikes, window):
    """Extract EPSPs at time `spikes` from voltage trace `v`.

    Args:
        t (numpy.ndarray): Time vector (ms).
        v (numpy.ndarray): Soma voltage trace. Must have the same size of `t` (mV).
        spikes (numpy.ndarray): Time of presynaptic spikes.
            Every value in `spikes` must be in the interval [min(`t`), max(`t`)] (ms).
        window (float): Size of EPS detection window in ms.

    Returns:
        numpy.ndarray: Vector of EPSPs (mV).

    Raises:
        RuntimeError: if a postsynaptic cell spike is found during a connectivity test
        RuntimeError: if the detection window can have multiple EPSPs in it
    """
    # Verify presence of only one EPSP in window
    if np.max(np.diff(spikes)) < window:
        raise RuntimeError("Only one EPSP should be present in the detection window")

    # Get EPSPs
    n = len(spikes)
    epsps = np.zeros(n)
    for i in range(n):
        w0 = np.searchsorted(t, spikes[i])  # Beginning of EPSP window
        vbaseline = v[w0]
        w1 = np.searchsorted(t, spikes[i] + window)  # End of EPSP window
        epspmaxidx = np.argmax(v[w0:w1]) + w0
        vepsp = v[epspmaxidx]
        # Abort if postsynaptic spike
        if vepsp > -30:
            raise RuntimeError("Postsynaptic cell spiking during connectivity test")
        # Compute epsps
        epsp = vepsp - vbaseline
        epsps[i] = epsp
    return epsps


def epsp_slope(vtrace):
    """Returns slope between points at [0.3, 0.75] * peak of given trace.

    Attention! This function expects that the trace is sampled (or interpolated)
    at a single timestep, since time is not taken into account during calculations.

    Args:
        vtrace (numpy.ndarray): interpolated voltage trace of one EPSP (mV)

    Returns:
        float: slope of the EPSP (mV)
    """
    # Remove baseline
    v = vtrace - vtrace[0]
    # Find peak
    peak = np.max(v)
    peak_idx = np.argmax(v)
    # Get 30% and 75% rise time indices
    idx0 = np.argmin(np.abs(v[:peak_idx] - 0.3 * peak))
    idx1 = np.argmin(np.abs(v[:peak_idx] - 0.75 * peak))
    # Get slope of fitting line between the two
    m = (v[idx1] - v[idx0]) / (idx1 - idx0)
    return m


class Experiment(object):
    """A full STDP induction experiment.

    The experiment consists of two connectivity tests (C01 and C02), separed
    by the induction protocol.

    Attributes:
        t (numpy.ndarray): Time vector (ms)
        v (numpy.ndarray): Soma voltage trace (ms)
        spikes (numpy.ndarray): Pre-synaptic spike times (ms)
        duration (dict): Duration of C01 and C02 phases (ms)
        period (float): The Cx period (ms)
        c01period (float): The C01 period (ms)
        c02period (float): The C02 period (ms)
        epspwindow (float): Size of EPS detection window (ms)
        cxs (list): Names of the Cx tests. These names are used as keys
            in the dictionaries (cxspikes, duration, epsp, cxtrace)
        cxspikes (dict): Pre-synaptic spikes times (ms)
            occuring during each test (C01 & C02)
    """

    def __init__(
        self,
        data,
        c01duration=40.0,
        c02duration=40.0,
        period=10.0,
        c01period=None,
        c02period=None,
    ):
        """Constructor.

        Args:
            data (str or dict): Path to simulation results file or results dictionary
            c01duration (float): Duration of C01 phase in minutes.
            c02duration (float): Duration of C02 phase in minutes.
            period (float): The Cx period in seconds.
            c01period (float): The C01 period in seconds. If None, period will be used.
            c02period (float): The C02 period in seconds. If None, period will be used.

        Raises:
            TypeError if data is neither a dictionary nor a string
        """
        if isinstance(data, dict):
            self.t = data["t"]
            self.v = data["v"]
            self.spikes = data["prespikes"]
        elif isinstance(data, str):
            h5file = h5py.File(data, "r")
            self.t = h5file["t"][()]
            self.v = h5file["v"][()]
            self.spikes = h5file["prespikes"][()]
            h5file.close()
        else:
            raise TypeError("data argument of Experiment has to be dict or str")
        # Store other attributes
        self.duration = {
            "C01": c01duration * 60 * 1000.0,  # min to ms
            "C02": c02duration * 60 * 1000.0,
        }  # min to ms
        self.period = period * 1000.0  # sec to ms
        self.c01period = (
            c01period * 1000.0 if c01period is not None else period * 1000.0
        )
        self.c02period = (
            c02period * 1000.0 if c02period is not None else period * 1000.0
        )
        # Create common attributes
        self.epspwindow = 100.0  # ms
        self.cxs = ["C01", "C02"]
        self.cxspikes = {
            "C01": self.spikes[: int(self.duration["C01"] / self.c01period)],
            "C02": self.spikes[-int(self.duration["C02"] / self.c02period) :],
        }

    @property
    def epsp(self):
        """Returns dict containing EPSP vectors for each test (mV)."""
        epsp = {
            cx: get_epsp_vector(self.t, self.v, self.cxspikes[cx], self.epspwindow)
            for cx in self.cxs
        }
        return epsp

    @property
    def cxtrace(self):
        """Returns time and interpolated trace of each EPSP as dict."""
        tdense = np.linspace(0, self.epspwindow, int(self.epspwindow / 0.025))
        cxtrace = {"t": tdense}
        for cx in self.cxs:
            cxtrace[cx] = []
            for s in self.cxspikes[cx]:
                idx0 = np.searchsorted(self.t, s)
                idx1 = np.searchsorted(self.t, s + self.epspwindow)
                vdense = np.interp(tdense + s, self.t[idx0:idx1], self.v[idx0:idx1])
                cxtrace[cx].append(vdense)
            cxtrace[cx] = np.array(cxtrace[cx])

        return cxtrace

    def compute_epsp_interval(self, interval):
        """Compute mean EPSP amplitude at regular intervals.

        Args:
            interval (float): The interval in minutes.

        Returns:
            dict: A dictionary of interval statistics for each Cx in Experiment.
        """
        results = {}
        for cx in self.cxs:
            n = int(self.duration[cx] / (interval * 60 * 1000.0))
            epsp_groups = np.split(self.epsp[cx], n)
            spike_groups = np.split(self.cxspikes[cx], n)
            avg = np.mean(epsp_groups, axis=1)
            sem = np.std(epsp_groups, axis=1) / np.sqrt(len(epsp_groups[0]))
            t = np.mean(spike_groups, axis=1)
            results[cx] = {"avg": avg, "sem": sem, "t": t}
        return results

    def compute_epsp_ratio(self, n, method="amplitude", full=False):
        """Compute mean EPSP change.

        Args:
            n (int): Number of sweeps in Cx to be considered for mean EPSP calculation
            method (str): Method used to compute EPSP ratio (amplitude or slope)
            full (bool): whether to return the mean value and std of epsp before and after
                cell stimulus in addition to the epsp ratio

        Returns:
            if full is False, returns

            - ratio_epsp (float): Mean EPSP change

            if full is True, returns a tuple containing

            - epsp_before (float): mean value of EPSP or slope of mean EPSP trace in test C01
            - epsp_after (float): mean value of EPSP or slope of mean EPSP trace in test C02
            - ratio_epsp (float): Mean EPSP change
            - epsp_before_std (float): std of EPSP in test C01 if method is amplitude, else 0
            - epsp_after_std (float): std of EPSP in test C02 if method is amplitude, else 0


        Raises:
            ValueError: if method is neither 'amplitude' nor 'slope'
        """
        if method == "amplitude":
            epsp_before = np.mean(self.epsp["C01"][-n:])
            epsp_before_std = np.std(self.epsp["C01"][-n:])
            epsp_after = np.mean(self.epsp["C02"][-n:])
            epsp_after_std = np.std(self.epsp["C02"][-n:])
        elif method == "slope":
            epsp_before = epsp_slope(np.mean(self.cxtrace["C01"][-n:], axis=0))
            epsp_before_std = 0
            epsp_after = epsp_slope(np.mean(self.cxtrace["C02"][-n:], axis=0))
            epsp_after_std = 0
        else:
            raise ValueError(f"Unknown method {method}")
        epsp_ratio = epsp_after / epsp_before
        if full:
            return epsp_before, epsp_after, epsp_ratio, epsp_before_std, epsp_after_std
        else:
            return epsp_ratio

    def normalize_time(self, t):
        """Normalize time vector `t`.

        Convert milliseconds to minutes and shift t = 0 to beginning of induction phase.

        Args:
            t (numpy.ndarray): Time vector (ms)

        Results:
            tnorm (numpy.ndarray): Normalized time vector (mn)
        """
        return (t - self.duration["C01"]) / (60.0 * 1000.0)
