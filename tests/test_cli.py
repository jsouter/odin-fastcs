import subprocess
import sys

from odin_fastcs import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "odin_fastcs", "--version"]
    stdout = subprocess.check_output(cmd).decode().strip().split("\n")
    assert __version__ in stdout
