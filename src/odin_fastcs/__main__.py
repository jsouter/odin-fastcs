from argparse import ArgumentParser

from fastcs.backends.asyncio_backend import AsyncioBackend
from fastcs.backends.epics.backend import EpicsBackend
from fastcs.connections import IPConnectionSettings
import asyncio
from typing import Any
from fastcs.mapping import Mapping
from . import __version__
from odin_fastcs.odin_controller import FPOdinController

__all__ = ["main"]


def get_controller() -> FPOdinController:
    tcont = FPOdinController(IPConnectionSettings("127.0.0.1", 8888))
    return tcont

def create_backend() -> EpicsBackend:
    tcont = get_controller()
    asyncio.run(tcont.connect())
    m = Mapping(tcont)
    return EpicsBackend(m)

def create_gui(backend) -> None:
    backend.create_gui()


def test_ioc(backend) -> None:
    ioc = backend.get_ioc()
    ioc.run()


def test_asyncio_backend() -> None:
    tcont = get_controller()
    m = Mapping(tcont)
    backend = AsyncioBackend(m)
    backend.run_interactive_session()


def main(args=None):
    parser = ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version=__version__)
    args = parser.parse_args(args)
    backend = create_backend()
    create_gui(backend)
    test_ioc(backend)


# test with: python -m odin_fastcs
if __name__ == "__main__":
    main()