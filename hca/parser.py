from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import json
import jsonpointer
import pprint

from .full_upload import FullUpload
from .full_download import FullDownload
from .constants import Constants

ADDED_COMMANDS = [FullUpload, FullDownload]


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


def _array_indexing(spec, param, hierarchy_clone, indexed_parameters):
    next_level = param["items"]
    _propogate_info(next_level, param)
    items = _recursive_indexing(spec, next_level, hierarchy_clone, indexed_parameters, arr=True)

    new_param = {
        "in": param["in"],
        "name": param["name"],
        "req": param["req"],
        "type": "string",
        "array": True,
    }
    metavar = []
    description = [param.get("description", "")]

    # If recursive_indexing returns a list, that means this is an array of objects. Iterate through
    # this list and update hierarchy_clone to reflect the order they'll be inputted on the console.
    # Each element must be a tuple to know if there's a need to parse booleans and numbers.
    # This will be used when parsing manually.
    if isinstance(items, list):
        items.sort(key=lambda x: x['name'])
        hierarchy_clone.append([(arg["name"], arg["type"]) for arg in items])
        new_param["hierarchy"] = hierarchy_clone

        for item in items:
            metavar.append(item["name"].upper())
            if 'description' in item:
                description.append("{}: {}".format(item['name'], item['description']))

    # If recursive_indexing doesn't return a list, we still need to indicate that we're in an array,
    # so add an empty list to this level of the hierarchy.
    else:
        new_param["type"] = items["type"]
        hierarchy_clone.append([])
        new_param["hierarchy"] = hierarchy_clone
        metavar.append(items["name"].upper())
        if 'description' in items:
            description.append(items['name'] + items['description'])

    new_param["metavar"] = Constants.OBJECT_SPLITTER.join(metavar)
    new_param['description'] = "\n".join(description)

    indexed_parameters[param["name"]] = new_param


def _recursive_indexing(spec, param, hierarchy, indexed_parameters={}, arr=False):
    hierarchy_clone = [x for x in hierarchy]
    # Don't add unnecessary levels to the hierarchy.
    if (len(hierarchy_clone) == 0 or hierarchy_clone[-1] != param["name"]) and param["name"] != "irrelevant":
        hierarchy_clone.append(param["name"])

    # De-reference json refs within file.
    if "$ref" in param:
        ref = jsonpointer.resolve_pointer(spec, param["$ref"][1:])
        _propogate_info(ref, param)
        return _recursive_indexing(spec, ref, hierarchy_clone, indexed_parameters, arr)

    # Possible swagger schemas that the cli hasn't accounted for.
    elif "type" not in param:
        raise Exception("Unhandled swagger schema error")

    # Handling nested arrays as input in the cli could be cumbersome. In the future
    # could possibly do some parsing of json-like inner-arrays but unclear if that would be
    # a necessary feature for the future.
    elif param['type'] == "array" and arr:
        raise ValueError("Nested arrays are not supported in the CLI")

    elif param['type'] == "array":
        _array_indexing(spec, param, hierarchy_clone, indexed_parameters)

    # Index each element in the object
    elif param["type"] == "object":
        # If there are no properties (undefined schema) and it's not an array, add each type
        if ("properties" not in param) and (not arr):
            param_name = param["name"]
            param['name'] = param_name
            param["array"] = arr
            param["hierarchy"] = hierarchy_clone
            indexed_parameters[param_name] = param
            return

        # If there are no properties and not within an array, we should just parse the input as json
        elif "properties" not in param:
            return []

        # If there are properties or it's within an array, loop through properties and add each.
        # Will be an empty list if it's an array there are no defined properties. In this case,
        # we should parse the input as json.
        object_indexed_params = []
        for (prop_name, payload) in param['properties'].items():
            payload["name"] = prop_name
            payload['req'] = param['req'] and prop_name in param["required"]
            payload["in"] = param["in"]
            object_indexed_params.append(_recursive_indexing(spec, payload, hierarchy_clone, indexed_parameters, arr))
        return object_indexed_params

    # If this within array, don't set the parameter because we set a parameter value in the array "if"
    elif arr:
        return param

    # Normal type - add it to indexed parameters.
    else:
        param_name = param['name']
        param['name'] = param_name
        param["array"] = arr
        param["hierarchy"] = hierarchy_clone
        indexed_parameters[param_name] = param


def index_parameters(spec, endpoint_info):
    """Map all parameters from parameter name -> parameter info."""
    indexed_parameters = {}
    if "parameters" in endpoint_info:
        for param in endpoint_info['parameters']:

            # Labelling req instead of required b/c objects have "required"
            # array to tell which args required. Can't overwrite.
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


def _label_path_args_required(path, endpoint_params, indexed_parameters):
    """
    For all positional arguments in an endpoint, determine if the argument is required.

    If an argument is not always required (i.e. get-files/{uuid} and get-files are both
    endpoints) then it will be labeled not required, but the endpoints it is required
    will be marked to assist the user when using the help option.
    """
    # Find and clean all path args.
    path_split = path.split("/")
    path_args = list(filter(lambda x: len(x) > 0 and x[0] == "{", path_split))
    path_args = list(map(lambda x: x[1: -1], path_args))

    positional = endpoint_params["positional"]
    for i in range(max(len(list(path_args)), len(list(positional)))):
        # If this path arg for this base route hasn't been seen, add it to possible args.
        if i >= len(positional):
            argument = path_args[i]
            argrequired = indexed_parameters[argument]['req']
            arg_params = indexed_parameters[argument]
            positional.append({
                "argument": argument,
                "required": argrequired and not endpoint_params["seen"],
                "required_for": [],  # see explanation below
                "description": arg_params.get("description", ""),
                "type": arg_params.get("type", None),
                "format": arg_params.get("format", None),
                "pattern": arg_params.get("pattern", None)
            })
        # If there are more args that weren't seen on this base route, mark then not
        # required because they're not used in every endpoint.
        elif i >= len(path_args):
            positional[i]["required"] = False

        # If the arg is required on this endpoint, add this endpoint to the list of
        # endpoints for which this arg is needed.
        if i < len(path_args) and indexed_parameters[path_args[i]]['req']:
            positional[i]['required_for'].append(path)


def _label_optional_args_required(path, endpoint_params, indexed_parameters):
    """
    For all optional arguments in an endpoint, determine if the argument is required.

    If an argument is not always required then it will be labeled not required, but the
    endpoints it is required will be marked to assist the user when using the help option.
    """
    options = endpoint_params["options"]

    # If in another endpoint with the same base route has a required option that's
    # missing from this endpoint, it's not required.
    for (param_name, param_data) in options.items():
        if param_name not in indexed_parameters:
            param_data['required'] = False

    for (param_name, param_data) in indexed_parameters.items():
        if param_data["in"] != "path":  # Only non-positional args
            argrequired = indexed_parameters[param_name]['req']
            if param_name not in options:
                arg_params = indexed_parameters[param_name]
                options[param_name] = {
                    "array": param_data["array"],
                    "required": argrequired and not endpoint_params["seen"],
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

            # If the arg is required on this endpoint, add this endpoint to the list of
            # endpoints for which this arg is needed.
            if argrequired:
                options[param_name]["required_for"].append(path)


def _get_arg_type(arg_type_string):
    argtype = None
    if arg_type_string == "integer":
        argtype = int
    elif arg_type_string == "boolean":
        argtype = bool
    elif arg_type_string == "number":
        argtype = float
    return argtype


def _get_action(arg_type_string):
    if arg_type_string == "object":
        return AddObject
    return "store"


class AddObject(argparse.Action):
    """Object to parse json objects."""

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(AddObject, self).__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, json.loads(values))


def _add_positional_args(subparser, endpoint_info):
    for positional_arg in endpoint_info["positional"]:
        h = create_help_statement(positional_arg)

        argtype = _get_arg_type(positional_arg["type"])

        subparser.add_argument(
            positional_arg["argument"],
            nargs=None if positional_arg["required"] else "?",
            help=h,
            type=argtype
        )


def _add_optional_args(subparser, endpoint_info):
    for (optional_name, optional_data) in endpoint_info["options"].items():
        h = create_help_statement(optional_data)

        argtype = _get_arg_type(optional_data["type"])
        actiontype = _get_action(optional_data["type"])

        optional_name_with_dashes = optional_name.replace("_", "-")
        subparser.add_argument(
            "--" + optional_name_with_dashes,
            dest=optional_name,  # So we can send correctly formatted objects to api.
            metavar=optional_data["metavar"],
            required=optional_data["required"],
            nargs="+" if optional_data['array'] else None,
            help=h,
            type=argtype,
            action=actiontype
        )


def get_parser(spec):
    """
    Return an argparse parser and a dict containing important argument details.

    :param spec: The swagger api specification used to generate parser.
    :return parser: The parser configured to the given api spec.
    :return param_holders: Important parameter information for each endpoint used in
                           parsing. Basic format is:
                           {
                                <endpoint-name>: {
                                    description: str,
                                    options: {
                                        <option-arg-name> {
                                            array: bool,
                                            description: str,
                                            format: str,
                                            hierarchy: list,
                                            in: str,
                                            metavar: str,
                                            pattern: str,
                                            required: bool,
                                            required_for: list,
                                            type: str}
                                        }
                                    },
                                    # Notice array b/c need to be ordered for path.
                                    positional: [
                                        <Each arg has same format as option arg>
                                    ],
                                    seen: bool  # for cli help - need to know what
                                                # arguments are required for which
                                                # endpoints.
                                }
                           }
    """
    parser = argparse.ArgumentParser(description=spec['info']['description'])
    subparsers = parser.add_subparsers(help='sub-command help')
    for command in ADDED_COMMANDS:
        command.add_parser(subparsers)
    param_holders = {}

    for path in spec['paths']:
        path_split = path.split("/")

        for http_method in spec['paths'][path]:
            endpoint_info = spec['paths'][path][http_method]
            endpoint_name = make_name(http_method, path_split)
            indexed_parameters = index_parameters(spec, endpoint_info)

            # Start tracking params if there's no current store.
            if endpoint_name not in param_holders:
                param_holders[endpoint_name] = {
                    "seen": False,
                    "positional": [],
                    "options": {},
                    "description": endpoint_info.get("description", "placeholder")
                }
            else:
                param_holders[endpoint_name]["seen"] = True

            # Add args to their base_route-indexed param_data object with requirement indications.
            _label_path_args_required(path, param_holders[endpoint_name], indexed_parameters)
            _label_optional_args_required(path, param_holders[endpoint_name], indexed_parameters)

    for (endpoint_name, endpoint_info) in param_holders.items():
        subparser = subparsers.add_parser(endpoint_name, help=endpoint_info["description"])
        _add_positional_args(subparser, endpoint_info)
        _add_optional_args(subparser, endpoint_info)

    return parser, param_holders
