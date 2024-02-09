from argparse import ArgumentParser

from fastcs.backends.asyncio_backend import AsyncioBackend
from fastcs.backends.epics.backend import EpicsBackend
from fastcs.connections import IPConnectionSettings
import asyncio
from typing import Any
from fastcs.mapping import Mapping
from fastcs.controller import Controller
from . import __version__
from odin_fastcs.odin_controller import FPOdinController, FROdinController, OdinDetectorController
from fastcs.backends.epics.ioc import EpicsIOCOptions
from fastcs.backends.epics.gui import EpicsGUIOptions

__all__ = ["main"]


def get_controller() -> FPOdinController:
    main_cont = Controller()
    frcont = FROdinController(IPConnectionSettings("127.0.0.1", 8888))
    main_cont.register_sub_controller(frcont)
    fpcont = FPOdinController(IPConnectionSettings("127.0.0.1", 8888))
    main_cont.register_sub_controller(fpcont)
    # fpmerlin = OdinDetectorController("merlin", IPConnectionSettings("127.0.0.1", 8888))
    # main_cont.register_sub_controller(fpmerlin)
    # only displays one controller at a time... (whichever one gets registered first/last)
    # return fpmerlin
    return main_cont


def create_backend() -> EpicsBackend:
    cont = get_controller()
    # asyncio.run(cont.connect())
    for sub_controller in cont.get_sub_controllers():
        asyncio.run(sub_controller.connect())
    m = Mapping(cont)
    return EpicsBackend(m)

def create_gui(backend, prefix) -> None:
    options = EpicsGUIOptions(prefix=prefix)
    backend.create_gui(options)


def test_ioc(backend, prefix) -> None:
    ioc = backend.get_ioc()
    options = EpicsIOCOptions(name=prefix)
    ioc.run(options)


# def test_asyncio_backend() -> None:
#     tcont = get_controller()
#     m = Mapping(tcont)
#     backend = AsyncioBackend(m)
#     backend.run_interactive_session()


def main(args=None):
    parser = ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version=__version__)
    args = parser.parse_args(args)
    backend = create_backend()
    prefix = "HQV-EA-MRLN-01"
    create_gui(backend, prefix)
    test_ioc(backend, prefix)

# test with: python -m odin_fastcs
if __name__ == "__main__":
    main()