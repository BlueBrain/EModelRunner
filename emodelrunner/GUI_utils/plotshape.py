# -*- coding: utf-8 -*-
"""Plot shape of neuron."""

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


# pylint: disable=too-many-arguments, too-many-locals, too-many-branches, no-member, import-error
from __future__ import unicode_literals  # for micrometer display
from matplotlib import cm
from neuron.gui2.utilities import _segment_3d_pts


def auto_aspect(ax):
    """Sets the x, y, and z range symmetric around the center.

    Args:
        ax (matplotlib.axes.Axes): axis
    """
    bounds = [ax.get_xlim(), ax.get_ylim()]
    half_delta_max = max([(item[1] - item[0]) / 2 for item in bounds])
    xmid = sum(bounds[0]) / 2
    ymid = sum(bounds[1]) / 2

    ax.set_xlim((xmid - half_delta_max, xmid + half_delta_max))
    ax.set_ylim((ymid - half_delta_max, ymid + half_delta_max))


def get_color_from_cmap(val, val_min, val_max, cmap):
    """Return color.

    Args:
        val (float): value to get color for from colormap (mV)
        val_min (int): minimum value of voltage for colormap (mV)
        val_max (int): minimum value of voltage for colormap (mV)
        cmap (matplotlib.colors.Colormap): colormap

    Returns:
        tuple: tuple of RGBA values indicating a color
    """
    if val_min >= val_max:
        return "black"
    val_range = val_max - val_min
    return cmap((min(max(val, val_min), val_max) - val_min) / (val_range))


def plot_shape(ax, xaxis, yaxis, zaxis, plot_3d, data, linewidth):
    """Plot shape and return line.

    Args:
        ax (matplotlib.axes.Axes): axis
        xaxis (int): indicate which data to plot on the x-axis (0 for x, 1 for y, 2 for z)
        yaxis (int): indicate which data to plot on the y-axis (0 for x, 1 for y, 2 for z)
        zaxis (int): indicate which data to plot on the z-axis (0 for x, 1 for y, 2 for z)
        plot_3d (bool): whether to plot in 3d or 2d
        data (list): list of (xs, ys, zs, diams) for each segment
        linewidth (float): width of line in shape plot

    Returns:
        matplotlib.lines.Line2D: the plotted line
    """
    if plot_3d:
        (line,) = ax.plot(
            data[xaxis],
            data[yaxis],
            data[zaxis],
            "-",
            linewidth=linewidth,
            color="black",
        )
    else:
        (line,) = ax.plot(
            data[xaxis],
            data[yaxis],
            "-",
            linewidth=linewidth,
            color="black",
        )

    return line


def set_labels(ax, xaxis, yaxis, zaxis, plot_3d):
    """Set labels.

    Args:
        ax (matplotlib.axes.Axes): axis
        xaxis (int): indicate which label to set on the x-axis (0 for x, 1 for y, 2 for z)
        yaxis (int): indicate which label to set on the y-axis (0 for x, 1 for y, 2 for z)
        zaxis (int): indicate which label to set on the z-axis (0 for x, 1 for y, 2 for z)
        plot_3d (bool): whether to plot in 3d or 2d
    """
    labels = ["x [μm]", "y [μm]", "z [μm]"]
    ax.set_xlabel(labels[xaxis])
    ax.set_ylabel(labels[yaxis])
    if plot_3d:
        ax.set_zlabel(labels[zaxis])


def get_morph_lines(
    ax,
    sim,
    val_min=-90,
    val_max=30,
    sections=None,
    variable="v",
    cmap=cm.plasma,
    do_plot=False,
    plot_3d=False,
    threshold_volt=4,
    threshold_volt_fine=25,
    old_vals=None,
    vals_last_draw=None,
    xaxis=2,
    yaxis=0,
    zaxis=1,
    linewidth=0.9,
):
    """Plots a 3D shapeplot.

    Args:
        ax(matplotlib.axes.Axes): axis
        sim (bluepyopt.ephys.simulators.NrnSimulator) simulator
        val_min (int): minimum value of voltage for colormap (mV)
        val_max (int): minimum value of voltage for colormap (mV)
        sections (list) list of h.Section() objects to be plotted.
            If None, all sections are loaded.
        variable (str): variable to be plotted. 'v' for voltage.
        cmap (matplotlib.colors.Colormap): colormap
        do_plot (bool): True to plot data. False to get actualised data.
        plot_3d (bool): set to True to plot the shape in 3D
        threshold_volt (int): voltage difference from which
            color should be changed on the cell shape. (mV)
        threshold_volt_fine (int): voltage difference from which
            display should be updated after a small simulation time
            to fine display rapid changes. (mV)
        old_vals (list): variable values at the last display
        vals_last_drawn (list): variable values the last time
            the morphology has been drawn (and not blitted).
        xaxis (int): indicate which data to plot on the x-axis (0 for x, 1 for y, 2 for z)
        yaxis (int): indicate which data to plot on the y-axis (0 for x, 1 for y, 2 for z)
        zaxis (int): indicate which data to plot on the z-axis (0 for x, 1 for y, 2 for z)
        linewidth (float): width of line in shape plot

    Returns:
        tuple containing

        - list: line objects making up shapeplot to update in figure
        - list: voltages previously plotted (mV)
        - bool: True to force the draw of figure, False to blit the figure
    """
    # Adapted from the NEURON package (fct _do_plot in __init__):
    # https://www.neuron.yale.edu/neuron/
    # where this part of the code was itself adapted from
    # https://github.com/ahwillia/PyNeuron-Toolbox/blob/master/PyNeuronToolbox/morphology.py
    # Accessed 2019-04-11, which had an MIT license

    # Default is to plot all sections.
    if sections is None:
        sections = list(sim.neuron.h.allsec())

    sim.neuron.h.define_shape()

    if do_plot:
        lines_list = []
    else:
        # get lines to be actualised
        lines_list = ax.lines

    lines_to_update = []
    vals = []

    # get lines and variable values at each segment
    for i, sec in enumerate(sections):
        # Plot each segment as a line
        if do_plot:
            all_seg_pts = _segment_3d_pts(sec)

            for seg, data in zip(sec, all_seg_pts):
                val = getattr(seg, variable)
                vals.append(val)

                line = plot_shape(ax, xaxis, yaxis, zaxis, plot_3d, data, linewidth)
                set_labels(ax, xaxis, yaxis, zaxis, plot_3d)

                if cmap:
                    col = get_color_from_cmap(val, val_min, val_max, cmap)
                    line.set_color(col)
                lines_list.append(line)

        else:
            for seg in sec:
                val = getattr(seg, variable)
                vals.append(val)

    if do_plot:
        auto_aspect(ax)

    if old_vals is None:
        old_vals = [100] * len(vals)

    force_draw = False
    if old_vals and cmap:
        for i, (val, old_val) in enumerate(zip(vals, old_vals)):
            if val is not None and abs(val - old_val) > threshold_volt:
                col = get_color_from_cmap(val, val_min, val_max, cmap)

                lines_list[i].set_color(col)
                lines_to_update.append(lines_list[i])

                old_vals[i] = val

                if (
                    vals_last_draw is not None
                    and abs(val - vals_last_draw[i]) > threshold_volt_fine
                ):
                    force_draw = True

    if force_draw:
        lines_to_update = lines_list

    return lines_to_update, old_vals, force_draw
