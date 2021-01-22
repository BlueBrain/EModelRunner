"""Creates .hoc from cell."""
import argparse
import os

from emodelrunner.load import load_config
from emodelrunner.create_cells import create_cell
from emodelrunner.create_hoc_tools import (
    create_synapse_hoc,
    create_simul_hoc,
    create_run_hoc,
)


def write_hoc(hoc_dir, hoc_file_name, hoc):
    """Write hoc file."""
    hoc_path = os.path.join(hoc_dir, hoc_file_name)
    with open(hoc_path, "w") as hoc_file:
        hoc_file.write(hoc)


def write_hocs(config, hoc, simul_hoc, run_hoc, run_hoc_filename, syn_hoc=None):
    """Write hoc files."""
    hoc_dir = config.get("Paths", "memodel_dir")

    # cell hoc
    hoc_file_name = config.get("Paths", "hoc_file")
    write_hoc(hoc_dir, hoc_file_name, hoc)

    # createsimulation.hoc
    simul_hoc_filename = config.get("Paths", "simul_hoc_file")
    write_hoc(hoc_dir, simul_hoc_filename, simul_hoc)

    # run.hoc
    write_hoc(hoc_dir, run_hoc_filename, run_hoc)

    # synapses hoc
    if syn_hoc is not None:
        syn_dir = config.get("Paths", "syn_dir")
        syn_hoc_filename = config.get("Paths", "syn_hoc_file")
        write_hoc(syn_dir, syn_hoc_filename, syn_hoc)


def get_hoc(config, syn_temp_name="hoc_synapses"):
    """Returns hoc file and emodel."""
    # get directories and filenames from config
    template_dir = config.get("Paths", "templates_dir")
    template = config.get("Paths", "create_hoc_template_file")

    # get cell
    cell, release_params, _ = create_cell(config)

    # get cell hoc
    cell_hoc = cell.create_custom_hoc(
        release_params,
        template=template,
        template_dir=template_dir,
        config=config,
        syn_temp_name=syn_temp_name,
    )

    simul_hoc = create_simul_hoc(
        template_dir=template_dir,
        template_filename="createsimulation.jinja2",
        config=config,
    )

    run_hoc = create_run_hoc(
        template_dir=template_dir, template_filename="run_hoc.jinja2", config=config
    )

    # get synapse hoc
    if cell.add_synapses:
        # get synapse hoc
        syn_hoc = create_synapse_hoc(
            template_dir=template_dir,
            template_filename="synapses.jinja2",
            config=config,
            gid=cell.gid,
            synapses_template_name=syn_temp_name,
        )
    else:
        syn_hoc = None

    return cell_hoc, syn_hoc, simul_hoc, run_hoc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--c",
        default=None,
        help="the name of the config file",
    )
    args = parser.parse_args()

    config_file = args.c
    run_hoc_filename_ = "run.hoc"
    config_ = load_config(filename=config_file)

    cell_hoc_, syn_hoc_, simul_hoc_, run_hoc_ = get_hoc(
        config=config_, syn_temp_name="hoc_synapses"
    )

    write_hocs(
        config_,
        cell_hoc_,
        simul_hoc_,
        run_hoc_,
        run_hoc_filename_,
        syn_hoc_,
    )
