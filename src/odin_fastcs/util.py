from typing import Any, Callable, Dict, List, Mapping, Tuple
Checker = Callable[[Any], bool]


def is_metadata_object(v: Any) -> bool:
    return isinstance(v, dict) and "writeable" in v and "type" in v


def is_not_dict(v: Any) -> bool:
    return not isinstance(v, dict)


# value_checker: method to determine if a dictionary value relates to an actual param
# value or if it is another dict with params nested inside.
def flatten_dict(
    dd: Mapping[str, Any],
    separator: str = "/",
    prefix: str = "",
    value_checker: Checker = is_not_dict,
) -> Dict[str, Any]:
    if not value_checker(dd):
        return {
            prefix + separator + k if prefix else k: v
            for kk, vv in dd.items()
            for k, v in flatten_dict(vv, separator, kk, value_checker).items()
        }
    else:
        return {prefix: dd}


def unflatten_dict(
    dd: Dict[str, Any], separator: str = "/", reverse_indexing: bool = False
) -> Mapping[str, Any]:
    output: Mapping[str, Any] = {}
    for key, val in dd.items():
        key_parts = key.split(separator)
        if reverse_indexing:
            key_parts = key_parts[::-1]
        subtree = output
        np = len(key_parts)
        for idx, part in enumerate(key_parts):
            if part not in subtree:
                subtree[part] = {}
            if idx + 1 == np:
                subtree[part] = val
            subtree = subtree[part]
    return output


def map_short_name_to_path_and_value(
    parameters: Mapping[str, Any], separator: str, value_checker: Checker = is_not_dict
) -> Dict[str, Tuple[str, Any]]:
    # flattens so that we end up with a dict with keys of api path and values of
    # required metadata needed to construct FastCS Attrs
    flattened = flatten_dict(parameters, separator, value_checker=value_checker)
    # then inverts the tree so that the least significant parts of the path are grouped
    # together, to make it easier to reduce the path names
    inverse_tree = unflatten_dict(flattened, separator, reverse_indexing=True)

    def get_name_mapping(
        tree: Mapping[str, Any],
        name_parts: List[str] = [],
        parts_needed: int = 1,
        mapping: Dict[str, str] = {},
    ) -> Dict[str, str]:
        for part, subtree in tree.items():
            name: List[str] = [part] + name_parts
            if value_checker(subtree):
                full_name = separator.join(name)
                short_name = "_".join(name[-parts_needed:])
                mapping[full_name] = short_name
            elif isinstance(subtree, dict):
                get_name_mapping(
                    subtree,  # type: ignore
                    name,
                    len(name) + 1 if len(subtree) > 1 else parts_needed,  # type: ignore
                    mapping,
                )
            else:
                raise TypeError(
                    f"Can not parse subtree {subtree} {type(subtree)} {name} {tree}"
                )
        return mapping

    output: Dict[str, Tuple[str, Any]] = {}
    # there has to be a simpler way to do this...
    for full_name, short_name in get_name_mapping(inverse_tree).items():
        output[short_name] = (full_name, flattened.get(full_name))
    return output


def get_by_path(config: Mapping[str, Any], path: str, delimiter: str = '/') -> Any:
    parts = path.split('/')
    if len(parts) == 1:
        return config[parts[0]]
    elif parts[0] in config:
        return get_by_path(config[parts[0]], delimiter.join(parts[1:]))
    else:
        raise ValueError(f"Could not retrieve {parts[-1]} from mapping.")
