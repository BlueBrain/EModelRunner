"""Style-related functions."""

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

import matplotlib as mpl


def get_style_cst():
    """Returns dict containing style vars such as colors.

    Returns:
        dict: style colors, font and width
    """
    style_dict = {}
    # font & width. has to be an attribute to be accessible.
    # somehow, entry font & width cannot be configurated with style.
    style_dict["base_font"] = "Helvetica 10"
    style_dict["entry_width"] = 8

    # BBP colors
    style_dict["light_blue"] = "#15D3FF"
    style_dict["blue"] = "#0B83CD"
    style_dict["deep_blue"] = "#050A58"
    style_dict["light_grey"] = "#F2F2F2"
    style_dict["grey"] = "#888888"
    style_dict["deep_grey"] = "#333333"
    style_dict["white"] = "#FFFFFF"

    return style_dict


def set_matplotlib_style():
    """Configure ticks & labels size."""
    mpl.rcParams["lines.color"] = get_style_cst()["blue"]
    mpl.rcParams["axes.labelsize"] = 8
    mpl.rcParams["xtick.labelsize"] = 8
    mpl.rcParams["ytick.labelsize"] = 8


def define_style(style):
    """Define the style for ttk objects.

    Args:
        style (ttk.Style): style
    """
    style_dict = get_style_cst()

    style.configure(
        "TButton",
        background=style_dict["white"],
        font=style_dict["base_font"],
    )

    style.configure(
        "ControlSimul.TButton",
        padding=6,
        relief="solid",
        background=style_dict["white"],
        foreground=style_dict["deep_blue"],
        font="Helvetica 16 bold",
        borderwidth=2,
        highlightbackground=style_dict["deep_blue"],  # border color?
    )

    style.map(
        "ControlSimul.TButton",
        foreground=[
            ("pressed", "!disabled", style_dict["blue"]),
            ("disabled", style_dict["grey"]),
        ],
    )

    style.configure("TFrame", background=style_dict["white"])
    style.configure(
        "Boxed.TFrame",
        background=style_dict["white"],
        relief="solid",
        bordercolor=style_dict["deep_blue"],
        borderwidth=4,
    )

    style.configure(
        "TRadiobutton",
        background=style_dict["white"],
        relief="flat",
        cursor="dot",
        borderwidth=0,
        selectcolor=style_dict["blue"],
        font=style_dict["base_font"],
    )

    style.map(
        "TRadiobutton",
        foreground=[
            ("selected", style_dict["blue"]),
            ("!selected", style_dict["deep_blue"]),
        ],
    )

    style.configure(
        "TLabel",
        foreground=style_dict["deep_blue"],
        background=style_dict["white"],
        font=style_dict["base_font"],
    )

    style.configure(
        "TEntry",
        foreground="black",
        background=style_dict["white"],
    )

    style.map(
        "TEntry",
        highlightcolor=[("focus", style_dict["blue"])],
        bordercolor=[("focus", style_dict["blue"])],
    )

    style.configure(
        "TCheckbutton",
        foreground=style_dict["deep_blue"],
        background=style_dict["white"],
        font=style_dict["base_font"],
    )

    style.map(
        "TCombobox",
        fieldbackground=[("!disabled", style_dict["white"])],
        background=[("!disabled", style_dict["white"])],
    )
