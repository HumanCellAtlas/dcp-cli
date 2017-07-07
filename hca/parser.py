from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import pprint


def make_name(http_method, path_split):
    """Name an endpoint."""
    # If the api needs file/write/{sdf} functionality, will become put-file-write
    name = [http_method]
    path_non_args = list(filter(lambda x: len(x) > 0 and x[0] != "{", path_split))
    for non_arg in path_non_args:
        name.append(non_arg)
    name = "-".join(name)
    return name


def index_parameters(endpoint_info):
    """Map all parameters from parameter name -> parameter info."""
    indexed_parameters = {}

    if "parameters" not in endpoint_info:
        return indexed_parameters

    for param in endpoint_info['parameters']:
        if "schema" in param:
            schema_params = param['schema']['properties']
            for schema_param_name in schema_params:
                param_name = param['name'] + "-" + schema_param_name
                payload = schema_params[schema_param_name]
                payload["name"] = param_name
                payload['required'] = False  # Placeholder before checking required array
                payload['in'] = param["in"]
                indexed_parameters[param_name] = payload
            for required_name in param['schema']['required']:
                param_name = param['name'] + "-" + required_name
                indexed_parameters[param_name]['required'] = True
        else:
            param_name = param['name']
            indexed_parameters[param_name] = param
    return indexed_parameters


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
            indexed_parameters = index_parameters(endpoint_info)

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
                    argrequired = indexed_parameters[argument]['required']
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

                if i < len(path_args) and indexed_parameters[path_args[i]]['required']:
                    positional[i]['required_for'].append(path)

            # Find optional args and label them required or not
            options = param_holders[endpoint_name]["options"]
            for (param_name, param_data) in options.items():
                if param_name not in indexed_parameters:
                    param_data['required'] = False
            for (param_name, param_data) in indexed_parameters.items():
                if param_data["in"] != "path":
                    argrequired = indexed_parameters[param_name]['required']
                    if param_name not in options:
                        arg_params = indexed_parameters[param_name]
                        options[param_name] = {
                            "required": argrequired and not param_holders[endpoint_name]["seen"],
                            "required_for": [],
                            "description": arg_params.get("description", ""),
                            "type": arg_params.get("type", None),
                            "format": arg_params.get("format", None),
                            "pattern": arg_params.get("pattern", None)
                        }
                    else:
                        options[param_name]['required'] = argrequired and options[param_name]['required']
                    if argrequired:
                        options[param_name]["required_for"].append(path)

    for (endpoint_name, endpoint_info) in param_holders.items():
        subparser = subparsers.add_parser(endpoint_name, help=endpoint_info["description"])
        for positional_arg in endpoint_info["positional"]:
            h = positional_arg['description'] + "\nRequired for endpoints with these arguments specified:\n"
            h = h + "\n".join(positional_arg['required_for'])
            subparser.add_argument(
                positional_arg['argument'],
                nargs=1 if positional_arg["required"] else "?",
                help=h
            )
        for (optional_name, optional_data) in endpoint_info["options"].items():
            h = optional_data['description'] + "\nRequired for endpoints with these arguments specified:\n"
            h = h + "\n".join(optional_data['required_for'])
            subparser.add_argument(
                "--" + optional_name,
                required=optional_data["required"],
                help=h
            )
    return parser
