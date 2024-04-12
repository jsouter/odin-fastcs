from fastcs.connections.ip_connection import IPConnectionSettings
from fastcs.attributes import AttrR, AttrRW, AttrW
from fastcs.datatypes import Int, Float, Bool, String
from dataclasses import dataclass
import asyncio
from fastcs.controller import Controller
from typing import Any, Dict, List
from odin_fastcs.http_connection import HTTPConnection
from fastcs.wrappers import command, scan
import logging
from fastcs.attributes import Handler
from odin_fastcs.util import (
    get_by_path,
    map_short_name_to_path_and_value,
    is_not_dict,
    is_metadata_object,
)

types = {"float": Float(), "int": Int(), "bool": Bool(), "str": String()}


class AdapterResponseError(Exception): ...


@dataclass
class ParamTreeHandler(Handler):
    path: str
    update_period: float = 0.2
    allowed_values: Dict[int, str] | None = None

    async def put(
        self,
        controller: Any,
        attr: AttrW[Any],
        value: Any,
    ) -> None:
        try:
            response = await controller._connection.put(self.path, value)
            if "error" in response:
                raise AdapterResponseError(response["error"])
        except Exception as e:
            logging.error(f"put failed: {e}", attr)

    async def update(
        self,
        controller: Any,
        attr: AttrR[Any],
    ) -> None:
        try:
            response = await controller._connection.get(self.path)
            value = response["value"]
            await attr.set(value)
        except Exception as e:
            logging.error(f"update loop failed: {e}", self.path)


@dataclass
class OdinConfigurationHandler(Handler):
    path: str
    update_period: float = 0.2

    async def update(self, controller: Any, attr: AttrR[Any]) -> None:
        try:
            value = get_by_path(controller._cached_config_params, self.path)
            await attr.set(value)
        except Exception as e:
            logging.error(f"update loop failed: {e}", self.path)


class OdinController(Controller):
    def __init__(
        self,
        settings: IPConnectionSettings,
        api_prefix: str,
        process_prefix: str,
        param_tree: bool = False,
        process_params: bool = False,
    ):
        super(OdinController, self).__init__()
        self._ip_settings = settings
        self._api_prefix = api_prefix
        self._process_prefix = process_prefix
        self._path = process_prefix
        self._cached_config_params = {}
        # used to determine if we need to connect the param tree or C++ params
        self._has_param_tree = param_tree
        self._has_process_params = process_params
        asyncio.run(self.initialise())

    async def initialise(self) -> None:
        self._connection = HTTPConnection(self._ip_settings.ip, self._ip_settings.port)
        self._connection.open()
        if self._has_param_tree:
            await self._connect_parameter_tree()
        if self._has_process_params:
            await self._connect_process_params()  # this will fail with merlin
        await self._connection.close()

    async def connect(self) -> None:
        for controller in self.get_sub_controllers():
            if isinstance(controller, OdinController):  # to satisfy mypy
                await controller.connect()
        self._connection.open()

    async def _connect_parameter_tree(self):
        response = await self._connection.get(self._api_prefix + "/config/param_tree")
        existing_members = dir(self)
        for param, entry in map_short_name_to_path_and_value(
            response["value"], "/", is_metadata_object
        ).items():
            full_path, metadata = entry
            if "writeable" in metadata and metadata["writeable"]:
                attr_class = AttrRW
            else:
                attr_class = AttrR
            if metadata["type"] not in types:
                logging.warning(
                    f"Could not add parameter {param} of type {metadata['type']}"
                )
                # this is really something I should handle here
                continue
            allowed = (
                metadata["allowed_values"] if "allowed_values" in metadata else None
            )
            attr = attr_class(
                types[metadata["type"]],
                handler=ParamTreeHandler(
                    f"{self._api_prefix}/{full_path}", allowed_values=allowed
                ),
            )
            attr_name = (
                self._process_prefix + "_" + param
                if param in existing_members
                else param
            )
            attr_name = attr_name.replace(".", "")
            # TODO: instead we should get the next lowest level part of the name, e.g.
            # config/hdf/path could become hdf_path not fp_path
            setattr(self, attr_name, attr)

    async def _connect_process_params(self):
        # from C++ client
        response = await self._connection.get(
            self._api_prefix + "/config/client_params"
        )
        self._cached_config_params = response["value"]
        for process, params in response["value"].items():
            if len(response["value"]) > 1:
                prefix = f"{self._process_prefix}{int(process) + 1}_"
            else:
                prefix = ""
            # this could take a long time with 100 pairs of processes.. oh well?
            output = map_short_name_to_path_and_value(params, "/", is_not_dict)
            for param, entry in output.items():
                full_path, value = entry  # bit janky
                type_name = type(value).__name__
                if type_name not in types:
                    logging.warning(f"Couldn't make {param} of type {type_name}")
                    continue
                value_type = types[type_name]
                attr = AttrR(  # only readable for time being
                    value_type,
                    handler=OdinConfigurationHandler(f"{process}/{full_path}"),
                    group=f"{self._process_prefix}{int(process)+1}".capitalize(),
                    # TODO: can we do subgroups? to handle multiple blocks
                    # when we have e.g. multiple frame processor processes
                )
                settable_path = f"{prefix}{param}"
                setattr(self, settable_path, attr)

    # @scan(0.2)
    @command()
    async def _update_configuration(self):
        if self._has_process_params:
            response = await self._connection.get(
                self._api_prefix + "/config/client_params"
            )
            self._cached_config_params = response["value"]


class OdinTopController(Controller):
    """
    Connects all sub controllers on connect
    """

    async def connect(self) -> None:
        for controller in self.get_sub_controllers():
            if isinstance(controller, Controller):  # to satisfy mypy
                await controller.connect()


class FPOdinController(OdinController):
    def __init__(self, settings: IPConnectionSettings, api: str = "0.1"):
        super(FPOdinController, self).__init__(
            settings, f"api/{api}/fp", "FP", param_tree=True, process_params=True
        )


class FROdinController(OdinController):
    def __init__(self, settings: IPConnectionSettings, api: str = "0.1"):
        super(FROdinController, self).__init__(
            settings, f"api/{api}/fr", "FR", param_tree=True, process_params=True
        )


class MLOdinController(OdinController):
    def __init__(self, settings: IPConnectionSettings, api: str = "0.1"):
        super(MLOdinController, self).__init__(
            settings,
            f"api/{api}/meta_listener",
            "ML",
            param_tree=True,
            process_params=False,
        )


class OdinDetectorController(OdinController):
    def __init__(
        self, adapter_name: str, settings: IPConnectionSettings, api: str = "0.1"
    ):
        super(OdinDetectorController, self).__init__(
            settings,
            f"api/{api}/{adapter_name}",
            adapter_name.capitalize(),
            param_tree=True,
            process_params=False,
        )
