from argparse import ArgumentParser

from fastcs.backends.epics.backend import EpicsBackend
from fastcs.backends.epics.gui import EpicsGUIOptions
from fastcs.backends.epics.ioc import EpicsIOCOptions
from fastcs.connections.ip_connection import IPConnectionSettings
from fastcs.mapping import Mapping

from odin_fastcs.odin_controller import (
    FPOdinController,
    FROdinController,
    MLOdinController,
    OdinTopController,
)

from . import __version__

__all__ = ["main"]


def get_controller() -> FPOdinController:
    main_cont = OdinTopController()
    frcont = FROdinController(IPConnectionSettings("127.0.0.1", 8888))
    main_cont.register_sub_controller(frcont)
    fpcont = FPOdinController(IPConnectionSettings("127.0.0.1", 8888))
    main_cont.register_sub_controller(fpcont)
    mlcont = MLOdinController(IPConnectionSettings("127.0.0.1", 8888))
    main_cont.register_sub_controller(mlcont)

    return main_cont


def create_backend() -> EpicsBackend:
    cont = get_controller()
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
    prefix = "HQV-EA-EIG-01"
    create_gui(backend, prefix)
    test_ioc(backend, prefix)


# test with: python -m odin_fastcs
if __name__ == "__main__":
    main()
