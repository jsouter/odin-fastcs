def flatten_dict(dd, separator ='/', prefix =''):
    return { prefix + separator + k if prefix else k : v
             for kk, vv in dd.items()
             for k, v in flatten_dict(vv, separator, kk).items()
             } if isinstance(dd, dict) else { prefix : dd }


# accepts a flattened dict with underscore separators??
def disambiguate(things, separator):
    output = flatten_dict(things, separator)
    inverse_tree = {}
    # this now works but is very ugly
    for key, val in output.items():
        key_parts = key.lower().split(separator)[::-1]
        subtree = inverse_tree
        np = len(key_parts)
        for idx, part in enumerate(key_parts):
            if part not in subtree:
                subtree[part] = {}
            if idx + 1 == np:
                subtree[part] = val
            subtree = subtree[part]
    def recurse_tree(tree, name_parts=[], degeneracy=1, mapping={}):
        for part, subtree in tree.items():
            name = [part] + name_parts
            if isinstance(subtree, dict):
                recurse_tree(subtree, name, len(name) + 1 if len(subtree.keys()) > 1 else degeneracy, mapping)
            else:
                full_name = separator.join(name)
                short_name = "_".join(name[-degeneracy:])
                mapping[full_name] = short_name
        return mapping
    mapping = recurse_tree(inverse_tree)
    for full_name, short_name in mapping.items():
        output[short_name] = (full_name, output.pop(full_name))
    return output

def is_metadata_object(d):
    return "writeable" in d and "type" in d

# accepts a flattened dict with underscore separators??
def disambiguate_param_tree(things, separator): # nasty, should try and make this more uniform
    output = dict(things)
    inverse_tree = {}
    # this now works but is very ugly
    for key, val in output.items():
        key_parts = key.lower().split(separator)[::-1]
        subtree = inverse_tree
        np = len(key_parts)
        for idx, part in enumerate(key_parts):
            if part not in subtree:
                subtree[part] = {}
            if idx + 1 == np:
                subtree[part] = val
            subtree = subtree[part]
    def recurse_tree(tree, name_parts=[], degeneracy=1, mapping={}):
        for part, subtree in tree.items():
            name = [part] + name_parts
            if isinstance(subtree, dict) and not is_metadata_object(subtree):
                recurse_tree(subtree, name, len(name) + 1 if len(subtree.keys()) > 1 else degeneracy, mapping)
            else:
                full_name = separator.join(name)
                short_name = "_".join(name[-degeneracy:])
                mapping[full_name] = short_name
        return mapping
    mapping = recurse_tree(inverse_tree)
    for full_name, short_name in mapping.items():
        output[short_name] = (full_name, output.pop(full_name))
    return output