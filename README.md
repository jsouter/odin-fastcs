[![CI](https://github.com/DiamondLightSource/odin-fastcs/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/odin-fastcs/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/DiamondLightSource/odin-fastcs/branch/main/graph/badge.svg)](https://codecov.io/gh/DiamondLightSource/odin-fastcs)
[![PyPI](https://img.shields.io/pypi/v/odin-fastcs.svg)](https://pypi.org/project/odin-fastcs)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Odin FastCS

FastCS support for the Odin detector software framework

Source          | <https://github.com/DiamondLightSource/odin-fastcs>
:---:           | :---:
PyPI            | `pip install odin-fastcs`
Docker          | `docker run ghcr.io/diamondlightsource/odin-fastcs:latest`
Documentation   | <https://diamondlightsource.github.io/odin-fastcs>
Releases        | <https://github.com/DiamondLightSource/odin-fastcs/releases>

## Development

Odin FastCS does not do much unless it has an Odin control server to talk to. It is
possible to test some functionality in isolation by dumping server responses and creating
tests that parse those responses. Responses can be dumped from various Odin systems and
tests written against them that can run in CI to ensure support for those systems is not
broken. The `tests/dump_server_response.py` helper script will generate json files for
each adapter in an Odin server to write tests against.

Testing against static files is quite restrictive, so a dummy development environment is
provided to give developers a consistent live deployment to possible to work against
while developing the code. To set this up, run `dev/configure.sh` with the path to an
odin-data install prefix and the path to a venv with odin-control and odin-data
installed. This will populate the dev config with your environment - these changes
should not be checked in. The dev deployment can then be run with `dev/start.sh`.

Currently Odin FastCS depends on branches of both odin-control and odin-data, so these
branches are provided in `dev/requirements.txt` for convenience. Make a venv and then
`pip install -r dev/requirements.txt` will give an environment that the control server
and meta writer can run in. For the frameProcessor and frameReceiver, check out the
fastcs-dev branch of odin-data and build. It is recommended to use the vscode CMake
configuration to do this.

If you need to run a dev version of any of the applications, stop that process in the
deployment and run/debug it manually. There is a vscode launch config for an odin server
using the same config as the dev deployment for this purpose.

At boot time, FastCS will generate UIs that can be opened in Phoebus. This is the
clearest way to see the PVs that have been generated for the Odin server. It is also
possible to run `dbl()` in the EPICS shell to print a flat list of PVs.

<!-- README only content. Anything below this line won't be included in index.md -->

See https://diamondlightsource.github.io/odin-fastcs for more detailed documentation.
