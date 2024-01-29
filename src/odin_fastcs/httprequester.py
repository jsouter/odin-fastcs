from fastcs.connections import HTTPConnection, IPConnectionSettings
from fastcs.attributes import AttrR, AttrRW, AttrW
from fastcs.datatypes import Int, Float, Bool, String
from dataclasses import dataclass
import asyncio
from fastcs.controller import Controller
from typing import Any
from fastcs.connections import DisconnectedError
from fastcs.mapping import Mapping
from fastcs.backends.epics.backend import EpicsBackend
from odin_fastcs.odin_controller import OdinController, OdinHandler



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
                        handler=OdinHandler("api/0.1/merlin/" + key),
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

    FPparams = (await controller.connection.get("api/0.1/fp/config/params"))
    print(FPparams)


    mapping = Mapping(controller)
    backend = EpicsBackend(mapping)
    backend.create_gui()
    ioc = backend.get_ioc()
    ioc.run()
    await controller.connection.close()


if __name__ in "__main__":
    asyncio.run(main())
