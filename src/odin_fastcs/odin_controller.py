from fastcs.connections import IPConnectionSettings
from fastcs.attributes import AttrR, AttrRW, AttrW
from fastcs.datatypes import Int, Float, Bool, String
from dataclasses import dataclass
import asyncio
from fastcs.controller import Controller
from typing import Any
from fastcs.connections import DisconnectedError
from odin_fastcs.http_connection import HTTPConnection
from fastcs.wrappers import command, scan
import logging
from fastcs.attributes import Handler
from odin_fastcs.util import flatten_dict, disambiguate, disambiguate_param_tree
types = {"float": Float(), "int": Int(), "bool": Bool(), "str": String()}

@dataclass
class ParamTreeHandler(Handler):
    name: str
    update_period: float = 0.2

    async def put(
        self,
        controller: Any,
        attr: AttrW,
        value: Any,
    ) -> None:
        try:
            print("putting", self.name, value)
            response = await controller.connection.put(self.name, value)
            print(self.name, response)
            await attr.set(response["value"])
            # how do we get the attr from the controller?
        except Exception as e:
            print(f"update loop failed: {e}", attr)

    async def update(
        self,
        controller: Any,
        attr: AttrR,
    ) -> None:
        # print("updating", self.name)
        try:
            response = await controller.connection.get(self.name)
            await attr.set(response["value"])
        except Exception as e:
            # print(f"update loop failed:{e}", self.name)
            ...

@dataclass
class OdinConfigurationHandler(Handler):
    flattened_path: str
    update_period: float = 0.2

    async def update(self, controller: Any, attr: AttrR) -> None:
        try:
            value = controller._cached_config_params[self.flattened_path]
            await attr.set(value)
        except Exception as e:
            print(f"update loop failed: {e}", attr)

class DisconnectedHTTPConnection:
    def __init__(self, *args, **kwargs):
        ...

    async def get(self, *args, **kwargs) -> str:
        raise DisconnectedError("No HTTP connection established")

    async def put(self, *args, **kwargs):
        raise DisconnectedError("No HTTP connection established")

    async def close(self):
        ...

class OdinController(Controller):
    def __init__(self, settings: IPConnectionSettings, prefix: str=None):
        super(OdinController, self).__init__()
        self._ip_settings = settings
        self._prefix = prefix
        self.connection = DisconnectedHTTPConnection()
        self._process_prefix = "UNKNOWN"
        self._cached_config_params = {}

    async def connect(self) -> None:
        self.connection = HTTPConnection(
            # self._ip_settings, headers={"Content-Type": None}
            # self._ip_settings, headers={"Content-Type": "application/json"}
            self._ip_settings.ip, self._ip_settings.port
        )
        self.connection.open()
        if self._prefix is None:
            logging.warning("No HTTP prefix provided")
            return
        await self._connect_parameter_tree()
        await self._connect_process_params()

    async def _connect_parameter_tree(self):
        # should use disambiguate here too?
        response = await self.connection.get(self._prefix + "/config/param_tree")
        output = disambiguate_param_tree(response["value"], "/")
        for param, entry in output.items():
            full_path, metadata = entry
            if "writeable" in metadata and metadata["writeable"]:
                attr_class = AttrRW
            else:
                attr_class = AttrR
            attr = attr_class(types[metadata["type"]],
                              handler=ParamTreeHandler(self._prefix + "/" + full_path))
            attr_name = self._process_prefix + "_" + param
            setattr(self, attr_name, attr)
        # for path, metadata in response["value"].items():
        #     settable_path = "_".join(path.split("/"))
        #     attr_class = AttrR
        #     if "writeable" in metadata and metadata["writeable"]:
        #         attr_class = AttrRW
        #     attr = attr_class(types[metadata["type"]],
        #                     handler=ParamTreeHandler(self._prefix + "/" + path))
        #     setattr(self, settable_path, attr)
    

    async def _connect_process_params(self):
        # from C++ client
        response = await self.connection.get(self._prefix + "/config/client_params")
        self._cached_config_params = flatten_dict(response["value"]) # this is probably pretty slow!!!
        for process, params in response["value"].items():
            prefix = f"{self._process_prefix}{int(process) + 1}"
            # this could take a long time with 100 pairs of processes.. oh well?
            output = disambiguate(params, separator="/")
            for param, entry in output.items():
                full_path, value = entry # bit janky
                type_name = type(value).__name__
                if type_name not in types:
                    logging.warning(f"Couldn't make {param} of type {type_name}")
                    continue
                value_type = types[type_name]
                attr = AttrR( # only readable for time being
                    value_type, handler=OdinConfigurationHandler(f"{process}/{full_path}")
                )
                settable_path = f"{prefix}_{param}"
                setattr(self, settable_path, attr)

    @scan(0.2)
    @command()
    async def _update_configuration(self):
        response = await self.connection.get(self._prefix + "/config/client_params")
        self._cached_config_params = flatten_dict(response["value"]) # this is probably pretty slow!!!








        # for process, params in result["value"].items():
        #     process = str(int(process) + 1)
        #     attr_class = AttrRW
        #     for key, value in flatten_dict(params, "_").items():
        #         print(key)
        #         typename = type(value).__name__
        #         if typename in types:
        #             value_type = types[typename]
        #             attr_name = self._process_prefix + process + "_" + key
        #             if len("MY-DEVICE-PREFIX:" + attr_name) >= 61: # needs to be a better test here!
        #                 # fastcs should handle the name shortening itself...
        #                 print('name too long', attr_name)
        #                 continue
        #             setattr(self, attr_name, attr_class(value_type)) # no handler for now! have to make a custom one...
        # # make sure to add in the functionality to the Handler to request configuration and then set from that dict.
                    

        # Should we make a separate block for each FR/FP process??
        # would be nice to pair them up so FR1/FP1 are together, maybe with a split down the middle
        # or something

    # def add_to_controller(controller, path, full_path, metadata):
    #     parts = path.split("/")
    #     if len(parts) == 1:
    #         attr_name = "_" + parts[0]
    #         # set AttrR instead of {} or whatever
    #         attr_class = AttrR
    #         if "writeable" in metadata and metadata["writeable"]:
    #             attr_class = AttrRW
    #         setattr(controller, attr_name, attr_class(types[metadata["type"]]))
    #     else:
    #         # sub controller, kind of weird, maybe can register
    #         attr_name = "_" + parts[0]
    #         if not hasattr(controller, attr_name):
    #             setattr(controller, attr_name, OdinProcessController())
    #         add_to_controller(getattr(controller, attr_name), "/".join(parts[1:]), full_path, metadata)
    # for path, metadata in result["value"].items():
    #     add_to_controller(controller, path, path, metadata)
    # print(controller._config._hdf._file._prefix, controller._config._hdf._file._path)

class FPOdinController(OdinController):
    def __init__(self, settings: IPConnectionSettings, api="0.1"):
        prefix = f"api/{api}/fp"
        super(FPOdinController, self).__init__(settings, prefix)
        self._process_prefix = "FP"

class OdinProcessController(Controller):
    ...