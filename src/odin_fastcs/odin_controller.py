import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from fastcs.attributes import AttrR, AttrRW, AttrW, Handler
from fastcs.connections.ip_connection import IPConnectionSettings
from fastcs.controller import Controller
from fastcs.datatypes import Bool, Float, Int, String
from fastcs.util import snake_to_pascal

from odin_fastcs.http_connection import HTTPConnection
from odin_fastcs.util import (
    create_odin_parameters,
)

types = {"float": Float(), "int": Int(), "bool": Bool(), "str": String()}

REQUEST_METADATA_HEADER = {"Accept": "application/json;metadata=true"}
IGNORED_ADAPTERS = ["od_fps", "od_frs", "od_mls"]


class AdapterResponseError(Exception): ...


@dataclass
class ParamTreeHandler(Handler):
    path: str
    update_period: float = 0.2
    allowed_values: dict[int, str] | None = None

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
            logging.error("Update loop failed for %s:\n%s", self.path, e)

    async def update(
        self,
        controller: Any,
        attr: AttrR[Any],
    ) -> None:
        try:
            response = await controller._connection.get(self.path)
            # TODO: Don't like this...
            value = response[self.path.split("/")[-1]]
            await attr.set(value)
        except Exception as e:
            logging.error("Update loop failed for %s:\n%s", self.path, e)





class OdinController(Controller):
    def __init__(
        self,
        connection: HTTPConnection,
        param_tree: dict[str, Any],
        api_prefix: str,
        process_prefix: str,
    ):
        super().__init__()

        self._connection = connection
        self._param_tree = param_tree
        self._api_prefix = api_prefix
        self._path = process_prefix

    async def _create_parameter_tree(self):
        parameters = create_odin_parameters(self._param_tree)

        for parameter in parameters:
            if "writeable" in parameter.metadata and parameter.metadata["writeable"]:
                attr_class = AttrRW
            else:
                attr_class = AttrR

            if parameter.metadata["type"] not in types:
                logging.warning(f"Could not handle parameter {parameter}")
                # this is really something I should handle here
                continue

            allowed = (
                parameter.metadata["allowed_values"]
                if "allowed_values" in parameter.metadata
                else None
            )

            if len(parameter.uri) >= 3:
                group = snake_to_pascal(
                    f"{parameter.uri[0].capitalize()}_{parameter.uri[1].capitalize()}"
                )
            else:
                group = None

            attr = attr_class(
                types[parameter.metadata["type"]],
                handler=ParamTreeHandler(
                    "/".join([self._api_prefix] + parameter.uri), allowed_values=allowed
                ),
                group=group,
            )

            setattr(self, parameter.name.replace(".", ""), attr)


class OdinTopController(Controller):
    """
    Connects all sub controllers on connect
    """

    API_PREFIX = "api/0.1"

    def __init__(self, settings: IPConnectionSettings) -> None:
        super().__init__()

        self._connection = HTTPConnection(settings.ip, settings.port)

        asyncio.run(self.initialise())

    async def initialise(self) -> None:
        self._connection.open()

        adapters: list[str] = (
            await self._connection.get(f"{self.API_PREFIX}/adapters")
        )["adapters"]

        for adapter in adapters:
            if adapter in IGNORED_ADAPTERS:
                continue

            # Get full parameter tree and split into parameters at the root and under
            # an index where there are N identical trees for each underlying process
            response: dict[str, Any] = await self._connection.get(
                f"{self.API_PREFIX}/{adapter}", headers=REQUEST_METADATA_HEADER
            )
            root_tree = {k: v for k, v in response.items() if not k.isdigit()}
            indexed_trees = {k: v for k, v in response.items() if k.isdigit()}

            odin_controller = OdinController(
                self._connection,
                root_tree,
                f"{self.API_PREFIX}/{adapter}",
                f"{adapter.upper()}",
            )
            await odin_controller._create_parameter_tree()
            self.register_sub_controller(odin_controller)

            for idx, tree in indexed_trees.items():
                odin_controller = OdinController(
                    self._connection,
                    tree,
                    f"{self.API_PREFIX}/{adapter}/{idx}",
                    f"{adapter.upper()}{idx}",
                )
                await odin_controller._create_parameter_tree()
                self.register_sub_controller(odin_controller)

        await self._connection.close()

    async def connect(self) -> None:
        self._connection.open()


class FPOdinController(OdinController):
    def __init__(self, settings: IPConnectionSettings, api: str = "0.1"):
        super().__init__(
            settings, f"api/{api}/fp", "FP", param_tree=True, process_params=False
        )


class FROdinController(OdinController):
    def __init__(self, settings: IPConnectionSettings, api: str = "0.1"):
        super().__init__(
            settings, f"api/{api}/fr", "FR", param_tree=True, process_params=True
        )


class MLOdinController(OdinController):
    def __init__(self, settings: IPConnectionSettings, api: str = "0.1"):
        super().__init__(
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
        super().__init__(
            settings,
            f"api/{api}/{adapter_name}",
            adapter_name.capitalize(),
            param_tree=True,
            process_params=False,
        )
