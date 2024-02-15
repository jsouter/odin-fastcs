from typing import Any, Dict, Tuple


def is_metadata_object(v):
    return isinstance(v, dict) and "writeable" in v and "type" in v


def is_not_dict(v):
    return not isinstance(v, dict)


# value_checker: method to determine if a dictionary value relates to an actual param
# value or if it is another dict with params nested inside.
def flatten_dict(dd, separator="/", prefix="", value_checker=is_not_dict):
    if not value_checker(dd):
        return {
            prefix + separator + k if prefix else k: v
            for kk, vv in dd.items()
            for k, v in flatten_dict(vv, separator, kk, value_checker).items()
        }
    else:
        return {prefix: dd}


def unflatten_dict(dd, separator="/", reverse_indexing=False):
    output = {}
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
    things, separator, value_checker=is_not_dict
) -> Dict[str, Tuple[str, Any]]:
    # flattens so that we end up with a dict with keys of api path and values of
    # required metadata needed to construct FastCS Attrs
    flattened = flatten_dict(things, separator, value_checker=value_checker)
    # then inverts the tree so that the least significant parts of the path are grouped
    # together, to make it easier to reduce the path names
    inverse_tree = unflatten_dict(flattened, separator, reverse_indexing=True)

    def get_name_mapping(tree, name_parts=[], degeneracy=1, mapping={}):
        for part, subtree in tree.items():
            name = [part] + name_parts
            if value_checker(subtree):
                full_name = separator.join(name)
                short_name = "_".join(name[-degeneracy:])
                mapping[full_name] = short_name
            elif isinstance(subtree, dict):
                get_name_mapping(
                    subtree,
                    name,
                    len(name) + 1 if len(subtree.keys()) > 1 else degeneracy,
                    mapping,
                )
            else:
                raise TypeError(
                    f"Can not parse subtree {subtree} {type(subtree)} {name} {tree}"
                )
        return mapping

    output = {}
    # there has to be a simpler way to do this...
    for full_name, short_name in get_name_mapping(inverse_tree).items():
        output[short_name] = (full_name, flattened.get(full_name))
    return output
