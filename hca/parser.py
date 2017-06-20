from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import pprint

import jsonpointer

def make_name(http_method, path_split):
    """Name an endpoint."""
    # If the api needs file/write/{sdf} functionality, will become put-file-write
    name = [http_method]
    path_non_args = list(filter(lambda x: len(x) > 0 and x[0] != "{", path_split))
    for non_arg in path_non_args:
        name.append(non_arg)
    name = "-".join(name)
    return name


def _propogate_info(next_level, param):
    """Helper to propogate these values into the next level of the data structure."""
    next_level["name"] = param["name"]
    next_level["req"] = param["req"]
    next_level["in"] = param["in"]


def _recursive_indexing(spec, param, hierarchy, indexed_parameters={}, prev_name="", arr=False):
    hierarchy_clone = [x for x in hierarchy]
    if (len(hierarchy_clone) == 0 or hierarchy_clone[-1] != param["name"]) and param["name"] != "irrelevant":
        hierarchy_clone.append(param["name"])

    if "$ref" in param:
        ref = jsonpointer.resolve_pointer(spec, param["$ref"][1:])
        _propogate_info(ref, param)
        return _recursive_indexing(spec, ref, hierarchy_clone, indexed_parameters, prev_name, arr)

    elif "type" not in param or "schema" in param:
        raise Exception("Unhandled swagger schema error")

    elif param['type'] == "array" and arr:
        raise ValueError("Nested arrays are not supported in the CLI")

    elif param['type'] == "array":
        next_level = param["items"]
        _propogate_info(next_level, param)
        items = _recursive_indexing(spec, next_level, hierarchy_clone, indexed_parameters, prev_name, arr=True)

        new_param = {
            "in": param["in"],
            "name": param["name"],
            "req": param["req"],
            "type": "string",
            "array": True,
        }
        metavar = []
        description = [param['description']] if "description" in param else []

        if isinstance(items, list):
            hierarchy_clone.append([arg["name"] for arg in items])
            new_param["hierarchy"] = hierarchy_clone

            for item in items:
                metavar.append(item["name"].upper())
                if 'description' in item:
                    description.append(item['name'] + item['description'])
        else:
            hierarchy_clone.append([])
            new_param["hierarchy"] = hierarchy_clone
            metavar.append(items["name"].upper())
            if 'description' in items:
                description.append(items['name'] + items['description'])

        new_param["metavar"] = ":".join(metavar)
        new_param['description'] = "\n".join(description)

        indexed_parameters[param["name"]] = new_param

    elif param["type"] == "object":
        object_indexed_params = []
        for (prop_name, payload) in param['properties'].items():
            payload["name"] = prop_name
            payload['req'] = param['req'] and prop_name in param["required"]
            payload["in"] = param["in"]
            object_indexed_params.append(_recursive_indexing(spec, payload, hierarchy_clone, indexed_parameters, prev_name, arr))
        return object_indexed_params

    elif arr:
        return param

    else:
        param_name = prev_name + param['name']
        param['name'] = param_name
        param["array"] = arr
        param["hierarchy"] = hierarchy_clone
        indexed_parameters[param_name] = param


def index_parameters(spec, endpoint_info):
    """Map all parameters from parameter name -> parameter info."""
    indexed_parameters = {}
    if "parameters" in endpoint_info:
        for param in endpoint_info['parameters']:
            param["req"] = param["required"]

            # Make sure parameter name is not extras.
            if param["in"] == "body":
                inner_param = param["schema"]
                inner_param["in"] = "body"
                inner_param["name"] = "irrelevant"
                inner_param['req'] = param['req']
                param = inner_param

            _recursive_indexing(spec, param, [], indexed_parameters)
    return indexed_parameters


def create_help_statement(endpoint_info):
    """Make the help statement for each command line argument."""
    h = endpoint_info['description'] + "\nRequired for endpoints with these arguments specified:\n"
    h = h + "\n".join(endpoint_info['required_for'])
    return h


def get_parser(spec):
    """Return a cli parser that adheres to the api defined in api_spec.json."""
    parser = argparse.ArgumentParser(description=spec['info']['description'])
    subparsers = parser.add_subparsers(help='sub-command help')
    param_holders = {}

    for path in spec['paths']:
        path_split = path.split("/")

        for http_method in spec['paths'][path]:
            endpoint_info = spec['paths'][path][http_method]
            endpoint_name = make_name(http_method, path_split)
            indexed_parameters = index_parameters(spec, endpoint_info)

            if endpoint_name not in param_holders:
                param_holders[endpoint_name] = {
                    "seen": False,
                    "positional": [],
                    "options": {},
                    "description": endpoint_info.get("description", "placeholder")
                }
            else:
                param_holders[endpoint_name]["seen"] = True

            # Find positional arguments and label them required or not
            path_args = list(filter(lambda x: len(x) > 0 and x[0] == "{", path_split))
            path_args = list(map(lambda x: x[1: -1], path_args))
            positional = param_holders[endpoint_name]["positional"]
            for i in range(max(len(list(path_args)), len(list(positional)))):
                if i >= len(positional):
                    argument = path_args[i]
                    argrequired = indexed_parameters[argument]['req']
                    arg_params = indexed_parameters[argument]
                    positional.append({
                        "argument": argument,
                        "required": argrequired and not param_holders[endpoint_name]["seen"],
                        "required_for": [],
                        "description": arg_params.get("description", ""),
                        "type": arg_params.get("type", None),
                        "format": arg_params.get("format", None),
                        "pattern": arg_params.get("pattern", None)
                    })
                elif i >= len(path_args):
                    positional[i]["required"] = False

                if i < len(path_args) and indexed_parameters[path_args[i]]['req']:
                    positional[i]['required_for'].append(path)

            # Find optional args and label them required or not
            options = param_holders[endpoint_name]["options"]
            for (param_name, param_data) in options.items():
                if param_name not in indexed_parameters:
                    param_data['required'] = False
            for (param_name, param_data) in indexed_parameters.items():
                if param_name == "object":
                    continue
                if param_data["in"] != "path":
                    argrequired = indexed_parameters[param_name]['req']
                    if param_name not in options:
                        arg_params = indexed_parameters[param_name]
                        options[param_name] = {
                            "array": param_data["array"],
                            "required": argrequired and not param_holders[endpoint_name]["seen"],
                            "required_for": [],
                            "description": arg_params.get("description", ""),
                            "type": arg_params.get("type", None),
                            "format": arg_params.get("format", None),
                            "pattern": arg_params.get("pattern", None),
                            "metavar": arg_params.get("metavar", None),
                            "in": arg_params.get("in", None),
                            "hierarchy": arg_params["hierarchy"]
                        }
                    else:
                        options[param_name]['required'] = argrequired and options[param_name]['required']

                    if argrequired:
                        options[param_name]["required_for"].append(path)

    for (endpoint_name, endpoint_info) in param_holders.items():
        subparser = subparsers.add_parser(endpoint_name, help=endpoint_info["description"])
        for positional_arg in endpoint_info["positional"]:
            h = create_help_statement(positional_arg)
            subparser.add_argument(
                positional_arg['argument'],
                nargs=None if positional_arg["required"] else "?",
                help=h,
                type=int if positional_arg["type"] == "integer" else None
            )
        for (optional_name, optional_data) in endpoint_info["options"].items():
            h = create_help_statement(optional_data)
            subparser.add_argument(
                "--" + optional_name,
                metavar=optional_data["metavar"],
                required=optional_data["required"],
                nargs="+" if optional_data['array'] else None,
                help=h,
                type=int if optional_data["type"] == "integer" else None
            )

    return parser, param_holders
