from fastcs.connections import HTTPConnection, IPConnectionSettings
from fastcs.attributes import AttrR, AttrRW, AttrW
from fastcs.datatypes import Int, Float, Bool, String
from dataclasses import dataclass
import asyncio
from fastcs.controller import Controller
from typing import Any
from fastcs.connections import DisconnectedError


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
    def __init__(self, settings: IPConnectionSettings):
        super(OdinController, self).__init__()
        self._ip_settings = settings
        self.connection = DisconnectedHTTPConnection()

    async def connect(self) -> None:
        self.connection = HTTPConnection(
            self._ip_settings, headers={"Content-Type": None}
        )


@dataclass
class OdinHandler:
    controller: OdinController
    name: str
    update_period: float = 0.2

    async def put(
        self,
        # attr: AttrW,
        value: Any,
    ) -> None:
        try:
            response = await self.controller.connection.put(self.name)
            # await attr.set(response["value"])
            # how do we get the attr from the controller?
        except Exception as e:
            print(f"update loop failed:{e}")

    async def update(
        self,
        # attr: AttrR,
    ) -> None:
        try:
            response = await self.controller.connection.get(self.name)
            # await attr.set(response["value"])
        except Exception as e:
            print(f"update loop failed:{e}")


async def main():
    ip_settings = IPConnectionSettings("127.0.0.1", 8888)
    controller = OdinController(ip_settings)
    await controller.connect()
    # result = await connection.get("api/0.1/merlin/status/state")
    # result = await connection.get("api/0.1/fp/config/hdf/acquisition_id")
    tree = (await controller.connection.get("api/0.1/merlin/config/param_tree"))[
        "value"
    ]
    types = {"float": Float(), "int": Int(), "bool": Bool(), "str": String()}
    idx = 0
    inverse_tree = {}
    # make recursive dict with keys split by / delimiter,
    # starting from the last element first (to help disambiguate attribute names)
    # and represent each attribute with a FastCS Attr instance
    for key, blob in tree.items():
        key_parts = key.lower().split("/")[::-1]
        subtree = inverse_tree
        np = len(key_parts)
        for idx, part in enumerate(key_parts):
            if part not in subtree:
                subtree[part] = {}
            if idx + 1 == np:
                attr_class = (
                    AttrRW if "writeable" in blob and blob["writeable"] else AttrR
                )
                if "type" in blob and blob["type"] in types:
                    subtree[part] = attr_class(
                        types[blob["type"]],
                        handler=OdinHandler(controller, "api/0.1/merlin/" + key),
                    # how can we set the handler to be the connection?
                    # I guess we pass it the controller but then it gets a bit weird and circular
                    )  # not generic enough, obviously
                else:
                    print("hmm something went wrong, fix this code", key_parts, blob)
                if "allowed_values" in blob:
                    print(key, blob["allowed_values"])
            subtree = subtree[part]

    debug_names = []

    def recurse_tree(tree, name_parts=[], degeneracy=1):
        for part, subtree in tree.items():
            name = [part] + name_parts
            if isinstance(subtree, AttrR):
                attr_name = "_".join(name[-degeneracy:])
                debug_names.append(attr_name)
                # we should also test if the attr_name is not already in __dict__?
                setattr(controller, attr_name, subtree)
            elif isinstance(subtree, dict):
                if len(subtree.keys()) > 1:
                    degeneracy2 = len(name) + 1  # this gives the level
                else:
                    degeneracy2 = degeneracy
                recurse_tree(subtree, name, degeneracy2)

    recurse_tree(inverse_tree)
    # print(debug_names)

    # see FastCS itself, Handler put and update SHOULD, i.e. MUST accept controller and attr as arguments
    # await controller.num_exposures.updater.update()
    # print(controller.num_exposures.updater.name)
    await controller.connection.close()


if __name__ in "__main__":
    asyncio.run(main())
