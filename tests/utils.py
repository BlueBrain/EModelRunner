"""Utils."""
from contextlib import contextmanager
import os
import subprocess


@contextmanager
def cwd(path):
    """Cwd function that can be used in a context manager."""
    old_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old_dir)


def compile_mechanisms():
    """Compile the mechanisms if they are not compiled yet."""
    if not os.path.isfile(os.path.join("x86_64", "special")):
        subprocess.call(["nrnivmodl", "mechanisms"])
