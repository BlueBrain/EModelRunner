"""Frame Classes for the GUI."""

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

# pylint: disable=wrong-import-position, too-many-ancestors, too-many-lines, import-error
import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
except ImportError:
    from matplotlib.backends.backend_tkagg import (
        NavigationToolbar2Tk as NavigationToolbar2TkAgg,
    )

from emodelrunner.GUI_utils.plotshape import get_morph_lines
from emodelrunner.GUI_utils.style import get_style_cst


def positive_int_callback(input_):
    """Accepts only digits or '' as entry.

    Args:
        input_ (str): input to check

    Returns:
        bool: True if input is an int or an empty string, False otherwise
    """
    return input_.isdigit() or input_ == ""


def float_callback(input_):
    """Accepts only a float or '' as entry.

    Args:
        input_ (str): input to check

    Returns:
        bool: True if input is a float or an empty string, False otherwise
    """
    if input_ != "":
        try:
            float(input_)
        except (ValueError, TypeError):
            return False
    return True


class ToolbarCustom(NavigationToolbar2TkAgg):
    """Matplotlib toolbar class."""

    def set_message(self, msg):
        """Do not show message. This is unstable.

        Args:
            msg (str): message
        """


class FrameSetIntFromEntry(ttk.Frame):
    """Frame containing an entry for input."""

    def __init__(self, parent, gui, attr_name, label):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            gui (GUI): main class containing main frames and simulation
            attr_name (str): attribute of gui.simulation that can be changed with the entry
            label (str): text describing the attribute to display
        """
        ttk.Frame.__init__(self, parent, style="TFrame")

        style_dict = get_style_cst()

        # label
        self.label = ttk.Label(self, text=f"{label}:")

        # to enforce only digits in entry
        self.reg = self.register(positive_int_callback)

        # string variable to be binded to entry
        self.sv = tk.StringVar()
        self.sv.set(str(getattr(gui.simulation, attr_name)))  # default value
        self.sv.trace_add(
            "write",
            lambda name, index, mode, sv=self.sv: self.get_value(gui, attr_name),
        )

        # entry
        self.entry = ttk.Entry(
            self,
            textvariable=self.sv,
            font=style_dict["base_font"],
            width=style_dict["entry_width"],
        )
        self.entry.config(validate="key", validatecommand=(self.reg, "%P"))

        # grid
        self.label.grid(row=0, column=0, sticky=tk.W)
        self.entry.grid(row=0, column=1, sticky=(tk.E))

        self.columnconfigure(1, weight=1)  # only center column grows

    def get_value(self, gui, attr_name):
        """Put input value in simulation attribute.

        Args:
            gui (GUI): main class containing main frames and simulation
            attr_name (str): attribute of gui.simulation that can be changed with the entry
        """
        value = self.entry.get()
        if value == "":
            value = 0
        try:
            setattr(gui.simulation, attr_name, int(value))
            gui.config_has_changed()
        except (ValueError, TypeError):
            tk.messagebox.showerror(
                f"Bad {attr_name} value",
                "Must be an int.",
            )

    def disable(self):
        """Set entry state to disabled."""
        self.entry.state(["disabled"])

    def enable(self):
        """Set entry state to not disabled."""
        self.entry.state(["!disabled"])


class FrameStepStimulus(ttk.Frame):
    """Frame containing step stimulus value input."""

    def __init__(self, parent, gui):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            gui (GUI): main class containing main frames and simulation
        """
        ttk.Frame.__init__(self, parent, style="TFrame")

        style_dict = get_style_cst()

        self.step_stim = tk.DoubleVar()
        self.step_stim.set(gui.simulation.step_stim)  # step1 is selected

        self.step_stim_title = ttk.Label(self, text="Select a Step Stimulus")

        self.steps = []
        for step_amp in gui.simulation.steps:
            protocol_step = ttk.Radiobutton(
                self,
                text=f"{step_amp:.3g} nA",
                variable=self.step_stim,
                value=step_amp,
                command=lambda: self.get_step_stim(gui),
            )
            self.steps.append(protocol_step)

        self.custom_step = ttk.Radiobutton(
            self,
            text="Custom stimulus [nA]: ",
            variable=self.step_stim,
            value=gui.simulation.step_stim,
            command=lambda: self.get_custom_step_stim(gui),
        )

        # to enforce only float in entry
        self.reg = self.register(float_callback)

        # string variable to be binded to entry
        self.sv = tk.StringVar()
        self.sv.set("0.0")  # default value
        self.sv.trace_add(
            "write",
            lambda name, index, mode, sv=self.sv: self.get_custom_step_stim(gui),
        )

        # entry
        self.custom_entry = ttk.Entry(
            self,
            textvariable=self.sv,
            font=style_dict["base_font"],
            width=style_dict["entry_width"],
        )
        self.custom_entry.config(validate="key", validatecommand=(self.reg, "%P"))
        self.custom_entry.state(["!disabled"])

        self.step_stim_title.grid(row=0, column=0, sticky=tk.W)
        self.custom_step.grid(row=1, column=0, sticky=tk.W)
        self.custom_entry.grid(row=1, column=1, sticky=tk.E)
        step_row = 1
        for protocol_step in self.steps:
            step_row += 1
            protocol_step.grid(row=step_row, column=0, sticky=tk.W)

        self.columnconfigure(1, weight=1)  # only center column grows
        for i in range(step_row + 1):
            self.rowconfigure(i, weight=1)

    def get_step_stim(self, gui):
        """Put selected step stim value into simulation attribute.

        Args:
            gui (GUI): main class containing main frames and simulation
        """
        self.custom_entry.state(["disabled"])

        value = self.step_stim.get()
        gui.simulation.step_stim = value
        gui.config_has_changed()

    def get_custom_step_stim(self, gui):
        """Enable input and put input value into simulation attribute.

        Args:
            gui (GUI): main class containing main frames and simulation
        """
        self.custom_entry.state(["!disabled"])

        value = self.custom_entry.get()
        if value == "":
            value = 0
        try:
            gui.simulation.step_stim = float(value)
            gui.config_has_changed()
        except (ValueError, TypeError):
            tk.messagebox.showerror(
                "Bad step stimulus value",
                "Must be a float.",
            )


class FrameHoldStimulus(ttk.Frame):
    """Frame containing holding stimulus value input."""

    def __init__(self, parent, gui):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            gui (GUI): main class containing main frames and simulation
        """
        ttk.Frame.__init__(self, parent, style="TFrame")

        style_dict = get_style_cst()

        self.hold_stim = tk.DoubleVar()
        self.hold_stim.set(gui.simulation.hypamp)  # default hold stim is selected

        self.hold_stim_title = ttk.Label(self, text="Select a Holding Stimulus")

        self.hypamps = []
        for amp in gui.simulation.hypamps:
            protocol_hypamp = ttk.Radiobutton(
                self,
                text=f"{amp:.3g} nA",
                variable=self.hold_stim,
                value=amp,
                command=lambda: self.get_hold_stim(gui),
            )
            self.hypamps.append(protocol_hypamp)

        self.custom_hold = ttk.Radiobutton(
            self,
            text="Custom stimulus [nA]: ",
            variable=self.hold_stim,
            value=gui.simulation.hypamp,
            command=lambda: self.get_custom_hold_stim(gui),
        )

        # to enforce only float in entry
        self.reg = self.register(float_callback)

        # string variable to be binded to entry
        self.sv = tk.StringVar()
        self.sv.set("0.0")  # default value
        self.sv.trace_add(
            "write",
            lambda name, index, mode, sv=self.sv: self.get_custom_hold_stim(gui),
        )

        # entry
        self.custom_entry = ttk.Entry(
            self,
            textvariable=self.sv,
            font=style_dict["base_font"],
            width=style_dict["entry_width"],
        )
        self.custom_entry.config(validate="key", validatecommand=(self.reg, "%P"))
        self.custom_entry.state(["!disabled"])

        self.hold_stim_title.grid(row=0, column=0, sticky=tk.W)
        self.custom_hold.grid(row=1, column=0, sticky=tk.W)
        self.custom_entry.grid(row=1, column=1, sticky=tk.E)
        hold_row = 1
        for protocol_hypamp in self.hypamps:
            hold_row += 1
            protocol_hypamp.grid(row=hold_row, column=0, sticky=tk.W)

        self.columnconfigure(1, weight=1)  # only center column grows
        for i in range(hold_row + 1):
            self.rowconfigure(i, weight=1)

    def get_hold_stim(self, gui):
        """Put selected holding stim value into simulation attribute.

        Args:
            gui (GUI): main class containing main frames and simulation
        """
        self.custom_entry.state(["disabled"])

        value = self.hold_stim.get()
        gui.simulation.hypamp = value
        gui.config_has_changed()

    def get_custom_hold_stim(self, gui):
        """Enable input and put input value into simulation attribute.

        Args:
            gui (GUI): main class containing main frames and simulation
        """
        self.custom_entry.state(["!disabled"])

        value = self.custom_entry.get()
        if value == "":
            value = 0
        try:
            gui.simulation.hypamp = float(value)
            gui.config_has_changed()
        except (ValueError, TypeError):
            tk.messagebox.showerror(
                "Bad holding stimulus value",
                "Must be a float.",
            )


class FrameStepProtocol(ttk.Frame):
    """Frame containing step stimulus-related input."""

    def __init__(self, parent, gui):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            gui (GUI): main class containing main frames and simulation
        """
        ttk.Frame.__init__(self, parent, style="TFrame")

        # step stimulus
        self.frame_step_stim = FrameStepStimulus(self, gui)
        self.frame_step_delay = FrameSetIntFromEntry(
            self, gui, "step_delay", "Step stimulus delay [ms]"
        )
        self.frame_step_duration = FrameSetIntFromEntry(
            self, gui, "step_duration", "Step stimulus duration [ms]"
        )

        # holding stimulus
        self.frame_hold_stim = FrameHoldStimulus(self, gui)
        self.frame_hold_step_delay = FrameSetIntFromEntry(
            self, gui, "hold_step_delay", "Holding stimulus delay [ms]"
        )
        self.frame_hold_step_duration = FrameSetIntFromEntry(
            self,
            gui,
            "hold_step_duration",
            "Holding stimulus duration [ms]",
        )

        # display on grid
        self.frame_step_stim.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.frame_step_delay.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.frame_step_duration.grid(row=2, column=0, sticky=(tk.W, tk.E))

        self.frame_hold_stim.grid(row=3, column=0, sticky=(tk.W, tk.E))
        self.frame_hold_step_delay.grid(row=4, column=0, sticky=(tk.W, tk.E))
        self.frame_hold_step_duration.grid(row=5, column=0, sticky=(tk.W, tk.E))

        self.columnconfigure(0, weight=1)
        for i in range(6):
            self.rowconfigure(i, weight=1)


class FrameProtocols(ttk.LabelFrame):
    """Frame containing protocol-related inputs."""

    def __init__(self, parent, gui, title):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            gui (GUI): main class containing main frames and simulation
            title (ttk.Label): frame title to display
        """
        ttk.LabelFrame.__init__(self, parent, style="Boxed.TFrame", labelwidget=title)

        self.frame_sim_duration = FrameSetIntFromEntry(
            self, gui, "total_duration", "Simulation time [ms]"
        )
        self.frame_step_protocol = FrameStepProtocol(self, gui)

        self.frame_sim_duration.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.frame_step_protocol.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=12)


class FrameConfig(ttk.Frame):
    """Frame containing all inputs."""

    def __init__(self, parent, gui):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            gui (GUI): main class containing main frames and simulation
        """
        ttk.Frame.__init__(self, parent, style="TFrame")

        title_config_fig = ttk.Label(self, text="Display configuration")
        self.frame_config_fig = FrameConfigFig(self, gui, title_config_fig)

        title_protocols = ttk.Label(
            self, text="Simulation & Step stimulus configuration"
        )
        self.frame_protocols = FrameProtocols(self, gui, title_protocols)

        self.frame_config_fig.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.frame_protocols.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=10)


class FrameButtons(ttk.Frame):
    """Frame containing buttons to (re-)start and pause simulation."""

    def __init__(self, parent, gui):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            gui (GUI): main class containing main frames and simulation
        """
        ttk.Frame.__init__(self, parent, style="TFrame")

        self.start_button = ttk.Button(
            self, text="Start", command=gui.start, style="ControlSimul.TButton"
        )

        self.pause_button = ttk.Button(
            self,
            text="Pause",
            command=gui.pause,
            state=tk.DISABLED,
            style="ControlSimul.TButton",
        )

        self.continue_button = ttk.Button(
            self,
            text="Continue",
            command=gui.continue_simul,
            state=tk.DISABLED,
            style="ControlSimul.TButton",
        )

        self.start_button.grid(row=0, column=0)
        self.pause_button.grid(row=0, column=1)
        self.continue_button.grid(row=0, column=2)

    def simul_running(self):
        """Disable continue button, enable pause button."""
        self.pause_button["state"] = tk.NORMAL
        self.continue_button["state"] = tk.DISABLED

    def simul_on_pause(self):
        """Disable pause button, enable continue button."""
        self.pause_button["state"] = tk.DISABLED
        self.continue_button["state"] = tk.NORMAL

    def simul_ended(self):
        """Disable pause & continue buttons."""
        self.pause_button["state"] = tk.DISABLED
        self.continue_button["state"] = tk.DISABLED


class FrameFigures(ttk.Frame):
    """Frame containing the morphology and the voltage figures."""

    def __init__(
        self,
        parent,
        simulation,
        plot_3d=False,
        toolbar_on=False,
        figsize="medium",
        val_min=-80,
        val_max=30,
    ):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            simulation (NeuronSimulation): contains simulation (and cell) data
            plot_3d (bool): set to True to plot the cell shapes in 3D
            toolbar_on (bool): set to True to display the matplotlib toolbars
            figsize (str): figures size. can be "small", "medium", or "large".
            val_min (int): minimum voltage for colormap
            val_max (int): maximum voltage for colormap
        """
        ttk.Frame.__init__(self, parent, style="TFrame")

        self.xaxis = 2  # z
        self.yaxis = 0  # x
        self.zaxis = 1  # y
        self.plot_3d = plot_3d
        self.figsize = figsize

        self.val_min = val_min
        self.val_max = val_max

        # ---
        # figure for neuron visualisation
        # ---
        fig_morph = Figure()
        if self.plot_3d:
            self.ax_morph = fig_morph.add_subplot(111, projection="3d")
        else:
            self.ax_morph = fig_morph.add_subplot(111)
            self.ax_morph.set_aspect(aspect=1)

        # get data and axis lims for left morph figure
        _, self.old_vals, _ = get_morph_lines(
            ax=self.ax_morph,
            sim=simulation.sim,
            val_min=self.val_min,
            val_max=self.val_max,
            do_plot=True,
            plot_3d=self.plot_3d,
            xaxis=self.xaxis,
            yaxis=self.yaxis,
            zaxis=self.zaxis,
        )
        self.vals_last_draw = self.old_vals.copy()

        # resize & adjust figure for not cutting axis
        self.set_fig_morph_display(fig_morph)

        # create canva
        self.canva_morph = FigureCanvasTkAgg(fig_morph, self)
        self.canva_morph.get_tk_widget().grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S)
        )

        # for interactive 3d rotating with mouse
        if self.plot_3d:
            self.get_interactive_3d_rotation(self.canva_morph, self.ax_morph)

        # ---
        # figure for neuron visualisation with synapses
        # ---
        fig_morph_syn = Figure()
        if self.plot_3d:
            self.ax_morph_syn = fig_morph_syn.add_subplot(111, projection="3d")
        else:
            self.ax_morph_syn = fig_morph_syn.add_subplot(111)
            self.ax_morph_syn.set_aspect(aspect=1)

        # get data and axis lims
        get_morph_lines(
            ax=self.ax_morph_syn,
            sim=simulation.sim,
            do_plot=True,
            cmap=None,
            plot_3d=self.plot_3d,
            xaxis=self.xaxis,
            yaxis=self.yaxis,
            zaxis=self.zaxis,
        )

        # resize & adjust figure for not cutting axis
        self.set_fig_morph_display(fig_morph_syn)

        # create canva
        self.canva_morph_syn = FigureCanvasTkAgg(fig_morph_syn, self)
        # save background for blit
        self.ax_morph_syn_bg = self.canva_morph_syn.copy_from_bbox(
            self.ax_morph_syn.bbox
        )
        self.canva_morph_syn.get_tk_widget().grid(
            row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S)
        )

        # for interactive 3d rotating with mouse
        if self.plot_3d:
            self.get_interactive_3d_rotation(self.canva_morph_syn, self.ax_morph_syn)

        # ---
        # figure for voltage evolution
        # ---
        fig_volt = Figure()
        self.ax_volt = fig_volt.add_subplot(111)
        self.set_axis(x_max=simulation.protocol.total_duration)

        # set fig size
        self.set_fig_volt_display(fig_volt)

        # create canva
        self.canva_volt = FigureCanvasTkAgg(fig_volt, self)
        self.canva_volt.get_tk_widget().grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S)
        )

        # add matplotlib toolbar
        if toolbar_on:
            self.set_toolbars()

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)

    def set_fig_morph_display(self, fig):
        """Set shape figure size and adjustment.

        Args:
            fig (matplotlib.figure.Figure): figure to adjust
        """
        if self.figsize == "small":
            fig.set_size_inches((3, 3))
        elif self.figsize == "large":
            fig.set_size_inches((5, 5))
        else:
            fig.set_size_inches((4, 4))
        if self.plot_3d:
            if self.figsize:
                fig.subplots_adjust(right=0.8, left=0.2)
            else:
                fig.subplots_adjust(right=0.85)
        else:
            fig.subplots_adjust(right=0.98, top=0.98, bottom=0.15, left=0.20)

    def set_fig_volt_display(self, fig):
        """Set shape figure size and adjustment.

        Args:
            fig (matplotlib.figure.Figure): figure to adjust
        """
        if self.figsize == "small":
            fig.set_size_inches((4.5, 2))
        elif self.figsize == "large":
            fig.set_size_inches((7.5, 3))
        else:
            fig.set_size_inches((6, 2.5))
        fig.subplots_adjust(bottom=0.2)  # to avoid the xlabel being cut

    def set_toolbars(self):
        """Set a matplotlib toolbar for each figure."""
        # self.ax_morph.format_coord = lambda x, y: ""
        toolbar_frame_morph = tk.Frame(self)
        toolbar_frame_morph.grid(row=1, column=0, sticky=tk.E)
        ToolbarCustom(self.canva_morph, toolbar_frame_morph)

        # self.ax_morph_syn.format_coord = lambda x, y: ""
        toolbar_frame_morph_syn = tk.Frame(self)
        toolbar_frame_morph_syn.grid(row=1, column=1, sticky=tk.E)
        ToolbarCustom(self.canva_morph_syn, toolbar_frame_morph_syn)

        # self.ax_volt.format_coord = lambda x, y: ""
        toolbar_frame_volt = tk.Frame(self)
        toolbar_frame_volt.grid(row=3, column=0, columnspan=2)
        ToolbarCustom(self.canva_volt, toolbar_frame_volt)

    @staticmethod
    def get_interactive_3d_rotation(canva, ax):
        """Connect events to canva to enable rotative 3d plots with mouse.

        Args:
            canva (matplotlib.backends.backend_tkagg.FigureCanvasTkAgg): canva
            ax (matplotlib.axes.Axes): axes
        """
        # pylint: disable=protected-access
        canva.mpl_connect("button_press_event", ax._button_press)
        canva.mpl_connect("button_release_event", ax._button_release)
        canva.mpl_connect("motion_notify_event", ax._on_move)

    def set_axis(self, x_min=0, x_max=3000, y_min=-90, y_max=40):
        """Set the voltage figure's axis.

        Args:
            x_min (float): min value on x axis
            x_max (float): max value on x axis
            y_min (float): min value on y axis
            y_max (float): max value on y axis
        """
        self.ax_volt.set_xlim([x_min, x_max])
        self.ax_volt.set_ylim([y_min, y_max])
        self.ax_volt.set_xlabel("t [ms]")
        self.ax_volt.set_ylabel("v [mV]")

    def check_change(self, root, simulation):
        """Checks the voltage change in the cell sections.

        Update display if change is significant.

        Args:
            root (tk.Tk): root of the GUI
            simulation (NeuronSimulation): contains simulation (and cell) data

        Returns:
            bool: True if the cell morphology with color-coded voltage figure has been updated
        """
        # here, update is True if any of the morph lines has a significant change of voltage.
        morph_lines, old_vals, update = get_morph_lines(
            ax=self.ax_morph,
            sim=simulation.sim,
            val_min=self.val_min,
            val_max=self.val_max,
            do_plot=False,
            old_vals=self.old_vals,
            vals_last_draw=self.vals_last_draw,
        )
        if update:
            self.old_vals = old_vals
            self.display(root, simulation, morph_lines)
            return True
        return False

    def display(self, root, simulation, morph_lines=None):
        """Update both figures display.

        Args:
            root (tk.Tk): root of the GUI
            simulation (NeuronSimulation): contains simulation (and cell) data
            morph_lines (list of matplotlib.Line2D): list of lines to be actualized
                if they already have been computed, else None
        """
        # get voltage data
        t, v = simulation.get_voltage()

        # update data in Line2D
        if self.ax_volt.lines:
            line = self.ax_volt.lines[0]
            line.set_xdata(t)
            line.set_ydata(v)
        else:
            (line,) = self.ax_volt.plot(t, v)

        # draw voltage plot to canva
        self.ax_volt.draw_artist(line)
        self.canva_volt.blit(self.ax_volt.bbox)

        # do not blit too much on top of figure, or else
        # 'older' lines tend to stack in the background
        # and bias the perceived color of the line.
        # so redraw everything when there is a big change in color
        if morph_lines is not None:
            for line in morph_lines:
                self.ax_morph.draw_artist(line)

            self.vals_last_draw = self.old_vals.copy()
            self.canva_morph.draw()
        else:
            morph_lines, self.old_vals, force_draw = get_morph_lines(
                ax=self.ax_morph,
                sim=simulation.sim,
                val_min=self.val_min,
                val_max=self.val_max,
                do_plot=False,
                old_vals=self.old_vals,
                vals_last_draw=self.vals_last_draw,
            )

            for line in morph_lines:
                self.ax_morph.draw_artist(line)
            if force_draw:
                self.canva_morph.draw()
                self.vals_last_draw = self.old_vals.copy()
            else:
                self.canva_morph.blit(self.ax_morph.bbox)

        # update tkinter display
        root.update()

    def update_syn_display(self, root, simulation, size_scatter=6):
        """Update the display of the synapses on the right figure.

        Args:
            root (tk.Tk): root of the GUI
            simulation (NeuronSimulation): contains simulation (and cell) data
            size_scatter (int): size of synapses for scatter plot
        """
        # get all synapses previously drawn
        drawn_syns = self.ax_morph_syn.collections
        # hide them before redrawing shape
        for syn in drawn_syns:
            syn.set_visible(False)
        self.canva_morph_syn.draw()  # redraw morphology
        # delete the synapses so that the list is not a big bunch of hidden accumulated synapses
        for syn in drawn_syns:
            self.ax_morph_syn.collections.remove(syn)
        # restore background as the morphology without synapses
        self.canva_morph_syn.restore_region(self.ax_morph_syn_bg)

        # create synapse scatterplot
        syn_scatterplot = {}
        for mtype, data in simulation.syn_display_data.items():
            if data:
                data = np.array(data)
                syn_x = data[:, self.xaxis]
                syn_y = data[:, self.yaxis]
                syn_cols = data[:, 3]
                syn_colors = ["red" if x == 1 else "orange" for x in syn_cols]
                if self.plot_3d:
                    syn_z = data[:, self.zaxis]
                    syn_scatterplot[mtype] = self.ax_morph_syn.scatter(
                        xs=syn_x,
                        ys=syn_y,
                        zs=syn_z,
                        s=size_scatter,
                        c=syn_colors,
                        alpha=1,
                    )
                else:
                    syn_scatterplot[mtype] = self.ax_morph_syn.scatter(
                        x=syn_x, y=syn_y, s=size_scatter, c=syn_colors, alpha=1
                    )
            else:
                syn_scatterplot[mtype] = None

        # draw selected synapses
        for mtype in simulation.available_pre_mtypes:
            if mtype in simulation.pre_mtypes and syn_scatterplot[mtype]:
                syn_scatterplot[mtype].set_visible(True)
                self.ax_morph_syn.draw_artist(syn_scatterplot[mtype])
            elif syn_scatterplot[mtype]:
                syn_scatterplot[mtype].set_visible(False)

        # 3d does not support blitting
        if self.plot_3d:
            self.canva_morph_syn.draw()
        # redrawing somehow draws synapse behind shape in 2d.
        else:
            self.canva_morph_syn.blit(self.ax_morph_syn.bbox)

        # update tkinter display
        root.update()

    def restart_volt(self):
        """Clean the voltage figure."""
        (line,) = self.ax_volt.plot([], [])
        self.ax_volt.draw_artist(line)
        self.canva_volt.draw_idle()


class FrameMain(ttk.Frame):
    """Frame containing Figures and launching button."""

    def __init__(self, parent, gui):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            gui (GUI): main class containing main frames and simulation
        """
        ttk.Frame.__init__(self, parent, style="TFrame")
        self.frame_buttons = FrameButtons(self, gui)
        self.frame_figures = FrameFigures(
            self, gui.simulation, gui.plot_3d, gui.toolbar_on, gui.figsize
        )

        self.frame_buttons.grid(row=0, column=0)
        self.frame_figures.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def display(self, root, simulation):
        """Update figures display.

        Args:
            root (tk.Tk): root of the GUI
            simulation (NeuronSimulation): contains simulation (and cell) data
        """
        self.frame_figures.display(root, simulation)

    def check_change(self, root, simulation):
        """Checks the voltage change in the cell sections.

        Update display if change is significant.

        Args:
            root (tk.Tk): root of the GUI
            simulation (NeuronSimulation): contains simulation (and cell) data

        Returns:
            bool: True if the cell morphology with color-coded voltage figure has been updated
        """
        return self.frame_figures.check_change(root, simulation)

    def update_syn_display(self, root, simulation):
        """Update the display of the synapses on the right figure.

        Args:
            Args:
            root (tk.Tk): root of the GUI
            simulation (NeuronSimulation): contains simulation (and cell) data
        """
        self.frame_figures.update_syn_display(root, simulation)

    def restart_volt(self):
        """Clean voltage figure."""
        self.frame_figures.restart_volt()

    def simul_on_pause(self):
        """Disable pause button, enable continue button."""
        self.frame_buttons.simul_on_pause()

    def simul_running(self):
        """Disable continue button, enable pause button."""
        self.frame_buttons.simul_running()

    def simul_ended(self):
        """Disable pause & continue buttons."""
        self.frame_buttons.simul_ended()


class FrameSynapses(ttk.LabelFrame):
    """Frame containing all inputs."""

    def __init__(self, parent, gui, title):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            gui (GUI): main class containing main frames and simulation
            title (ttk.Label): frame title to display
        """
        ttk.LabelFrame.__init__(self, parent, style="Boxed.TFrame", labelwidget=title)

        style_dict = get_style_cst()

        # -- labels --
        self.labels = []
        self.labels.append(ttk.Label(self, text="Synapses"))
        self.labels.append(ttk.Label(self, text="Start time [ms]"))
        self.labels.append(ttk.Label(self, text="Spike Interval [ms]"))
        self.labels.append(ttk.Label(self, text="Spike number"))
        self.labels.append(ttk.Label(self, text="Noise"))

        for i, label in enumerate(self.labels):
            label.grid(row=0, column=i)
            self.columnconfigure(i, weight=1)

        self.rowconfigure(0, weight=1)

        # -- synapses --
        self.reg = self.register(positive_int_callback)

        self.mtype_buttons = []
        self.var_list = []  # 0 or 1 for each button / checkbox values
        self.id_list = []
        self.svs = []  # entries (start, interval, number, noise) values

        # list of lists : start, interval, number and noise
        self.entries = [[] for x in range(4)]

        # -- create buttons & parameter entries --
        for i, id_ in enumerate(gui.simulation.available_pre_mtypes.keys()):
            # pre-cell m-types
            self.var_list.append(tk.IntVar())
            self.var_list[i].set(0)
            self.id_list.append(id_)
            self.mtype_buttons.append(
                ttk.Checkbutton(
                    self,
                    text=gui.simulation.available_pre_mtypes[id_],
                    variable=self.var_list[i],
                    command=lambda: self.load_current_mtype_list(gui),
                    offvalue=0,
                    onvalue=1,
                )
            )
            # synapse start, interval, number, noise
            for j, entry in enumerate(self.entries):
                self.svs.append(tk.StringVar())
                entry.append(
                    ttk.Entry(
                        self,
                        textvariable=self.svs[4 * i + j],
                        font=style_dict["base_font"],
                        width=style_dict["entry_width"],
                    )
                )
                entry[i].config(validate="key", validatecommand=(self.reg, "%P"))
                entry[i].state(["disabled"])

            # set string variables
            self.set_svs(gui, i)

        # -- add buttons & entries on the grid --
        for i, (b, e1, e2, e3, e4) in enumerate(
            zip(*[self.mtype_buttons] + self.entries)
        ):
            b.grid(row=i + 1, column=0, sticky=(tk.W, tk.E), padx=2)
            e1.grid(row=i + 1, column=1, sticky=(tk.E), padx=2)
            e2.grid(row=i + 1, column=2, sticky=(tk.E), padx=2)
            e3.grid(row=i + 1, column=3, sticky=(tk.E), padx=2)
            e4.grid(row=i + 1, column=4, sticky=(tk.E), padx=2)
            self.rowconfigure(i + 1, weight=1)

    def toggle_button(self):
        """Enable/disable entries depending on the button status."""
        for i, var in enumerate(self.var_list):
            if var.get():
                for entry in self.entries:
                    entry[i].state(["!disabled"])
            else:
                for entry in self.entries:
                    entry[i].state(["disabled"])

    def set_svs(self, gui, i):
        """Returns the entry and the variable associated.

        Args:
            gui (GUI): main class containing main frames and simulation
            i (int): mtype index
        """
        # pylint: disable=cell-var-from-loop
        default_var = [
            gui.simulation.syn_start,
            gui.simulation.syn_interval,
            gui.simulation.syn_nmb_of_spikes,
            gui.simulation.syn_noise,
        ]
        for j, var in enumerate(default_var):
            self.svs[4 * i + j].set(str(var))
            self.svs[4 * i + j].trace_add(
                "write",
                lambda name, index, mode, sv=self.svs[
                    4 * i + j
                ]: self.load_current_mtype_list(gui),
            )

    @staticmethod
    def check_variable(x):
        """Returns the variable if it is a positive int. Returns 0 if not.

        Args:
            x (str): variable to check

        Returns:
            int: the variable if it is a positive int
        """
        try:
            if x == "":
                x = 0
            else:
                x = int(x)
                assert x >= 0
        except (ValueError, TypeError, AssertionError):
            tk.messagebox.showerror(
                "Bad parameter value",
                "Must be a positive int.",
            )
            x = 0
        return x

    def load_current_mtype_list(self, gui):
        """Load current mtype list and netstim params.

        Args:
            gui (GUI): main class containing main frames and simulation
        """
        gui.simulation.pre_mtypes = []
        gui.simulation.netstim_params = {}

        for idx, var, e1, e2, e3, e4 in zip(
            *[self.id_list, self.var_list] + self.entries
        ):
            if var.get():
                gui.simulation.pre_mtypes.append(idx)
                v1 = self.check_variable(e1.get())
                v2 = self.check_variable(e2.get())
                v3 = self.check_variable(e3.get())
                v4 = self.check_variable(e4.get())
                params = [v1, v2, v3, v4]
                # synapse netstim param depending on mtype
                # {mtypeidx:[start, interval, number, noise]}
                gui.simulation.netstim_params[idx] = params
        self.toggle_button()
        gui.frames["FrameMain"].update_syn_display(gui.root, gui.simulation)
        gui.config_has_changed()


class FrameConfigFig(ttk.LabelFrame):
    """Frame containing choices for figure display, such as 2d/3d or enabling toolbar."""

    def __init__(self, parent, gui, title):
        """Constructor.

        Args:
            parent (ttk.Frame): parent frame in which to embed this frame
            gui (GUI): main class containing main frames and simulation
            title (ttk.Label): frame title to display
        """
        ttk.LabelFrame.__init__(self, parent, style="Boxed.TFrame", labelwidget=title)

        # 2d / 3d radiobuttons
        self.plot_3d_var = tk.IntVar()
        self.plot_3d_var.set(int(gui.plot_3d))  # default hold stim is selected

        self.plot_2d_button = ttk.Radiobutton(
            self,
            text="2D neuron shape",
            variable=self.plot_3d_var,
            value=0,
            command=lambda: self.load_plot_3d_value(gui),
        )

        self.plot_3d_button = ttk.Radiobutton(
            self,
            text="3D neuron shape",
            variable=self.plot_3d_var,
            value=1,
            command=lambda: self.load_plot_3d_value(gui),
        )

        # toolbar checkbutton
        self.toolbar_var = tk.IntVar()
        self.toolbar_var.set(int(gui.toolbar_on))
        self.toolbar_button = ttk.Checkbutton(
            self,
            text="display figures toolbars",
            variable=self.toolbar_var,
            command=lambda: self.load_toolbar_value(gui),
            offvalue=0,
            onvalue=1,
        )

        # figsize choice
        self.figsize_var = tk.StringVar()
        self.figsize_var.set(str(gui.figsize))
        self.figsize_label = ttk.Label(self, text="Figure size:")
        self.figsize_small_button = ttk.Radiobutton(
            self,
            text="small",
            variable=self.figsize_var,
            value="small",
            command=lambda: self.load_figsize_value(gui),
        )

        self.figsize_medium_button = ttk.Radiobutton(
            self,
            text="medium",
            variable=self.figsize_var,
            value="medium",
            command=lambda: self.load_figsize_value(gui),
        )

        self.figsize_large_button = ttk.Radiobutton(
            self,
            text="large",
            variable=self.figsize_var,
            value="large",
            command=lambda: self.load_figsize_value(gui),
        )

        # put buttons on grid
        self.plot_2d_button.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E))
        self.plot_3d_button.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E))
        self.toolbar_button.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))
        self.figsize_label.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        self.figsize_small_button.grid(row=4, column=0, sticky=(tk.W, tk.E))
        self.figsize_medium_button.grid(row=4, column=1, sticky=(tk.W, tk.E))
        self.figsize_large_button.grid(row=4, column=2, sticky=(tk.W, tk.E))

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

    def load_toolbar_value(self, gui):
        """Change toolbar value in gui and reload figure frame.

        Args:
            gui (GUI): main class containing main frames and simulation
        """
        if self.toolbar_var.get():
            gui.toolbar_on = True
        else:
            gui.toolbar_on = False

        gui.reload_figure_frame()

    def load_plot_3d_value(self, gui):
        """Change figure display in gui and reload figure frame.

        Args:
            gui (GUI): main class containing main frames and simulation
        """
        if self.plot_3d_var.get():
            gui.plot_3d = True
        else:
            gui.plot_3d = False

        gui.reload_figure_frame()

    def load_figsize_value(self, gui):
        """Change figure size in gui and reload figure frame.

        Args:
            gui (GUI): main class containing main frames and simulation
        """
        gui.figsize = self.figsize_var.get()
        gui.reload_figure_frame()
