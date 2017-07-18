from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import shutil

from jinja2 import FileSystemLoader, Environment
import jsonpointer
import requests

from .constants import Constants


def _separator_to_camel_case(separated, separator):
    components = separated.split(separator)
    return "".join(x.title() for x in components)


def _get_spec(test_api_path=None):
    """
    Load the API specification.

    self.test_api_path is a path to the test api path if the functionality is being tested.
        api_spec is the spec downloaded from the api on build.
        ../test/test is the mocked up spec I've been toying with.
    :return:     The dictionary containing all swagger specification definitions.
    """
    if test_api_path:
        with open(test_api_path) as fp:
            api_spec_dict = json.load(fp)
    else:
        api_spec_dict = requests.get("https://hca-dss.czi.technology/v1/swagger.json").json()
    return api_spec_dict


def _make_name(http_method, path_split):
    """Name an endpoint."""
    # If the api needs file/write/{sdf} functionality, will become put-file-write
    name = [http_method]
    path_non_args = list(filter(lambda x: len(x) > 0 and x[0] != "{", path_split))
    for non_arg in path_non_args:
        name.append(non_arg)
    name = "-".join(name)
    return name


def _propagate_info(next_level, param):
    """Helper to propagate these values into the next level of the data structure."""
    for key in ("name", "req", "in"):
        next_level[key] = param[key]


def _array_indexing(spec, param, hierarchy_clone, indexed_parameters):
    next_level = param['items']
    _propagate_info(next_level, param)
    items = _recursive_indexing(spec, next_level, hierarchy_clone, indexed_parameters, arr=True)

    new_param = {
        'in': param['in'],
        'name': param['name'],
        'req': param['req'],
        'type': 'string',
        'array': True,
    }
    metavar = []
    description = [param.get('description', '')]

    # If recursive_indexing returns a list, that means this is an array of objects. Iterate through
    # this list and update hierarchy_clone to reflect the order they'll be inputted on the console.
    # Each element must be a tuple to know if there's a need to parse booleans and numbers.
    # This will be used when parsing manually.
    if isinstance(items, list):
        items.sort(key=lambda x: x['name'])
        hierarchy_clone.append([(arg['name'], arg['type']) for arg in items])
        new_param['hierarchy'] = hierarchy_clone

        for item in items:
            metavar.append(item['name'].upper())
            if 'description' in item:
                description.append("{}: {}".format(item['name'], item['description']))

    # If recursive_indexing doesn't return a list, we still need to indicate that we're in an array,
    # so add an empty list to this level of the hierarchy.
    else:
        new_param['type'] = items['type']
        hierarchy_clone.append([])
        new_param['hierarchy'] = hierarchy_clone
        metavar.append(items['name'].upper())
        if 'description' in items:
            description.append(items['name'] + items['description'])

    new_param['metavar'] = Constants.OBJECT_SPLITTER.join(metavar)
    new_param['description'] = "\n".join(description)

    indexed_parameters[param["name"]] = new_param


def _recursive_indexing(spec, param, hierarchy, indexed_parameters={}, arr=False):
    hierarchy_clone = [x for x in hierarchy]
    # Don't add unnecessary levels to the hierarchy.
    if (len(hierarchy_clone) == 0 or hierarchy_clone[-1] != param['name']) and param['name'] != 'irrelevant':
        hierarchy_clone.append(param['name'])

    # De-reference json refs within file.
    if '$ref' in param:
        ref = jsonpointer.resolve_pointer(spec, param['$ref'][1:])
        _propagate_info(ref, param)
        return _recursive_indexing(spec, ref, hierarchy_clone, indexed_parameters, arr)

    # Possible swagger schemas that the cli hasn't accounted for.
    elif 'type' not in param:
        raise Exception("Unhandled swagger schema error")

    # Handling nested arrays as input in the cli could be cumbersome. In the future
    # could possibly do some parsing of json-like inner-arrays but unclear if that would be
    # a necessary feature for the future.
    elif param['type'] == "array" and arr:
        raise ValueError("Nested arrays are not supported in the CLI")

    elif param['type'] == "array":
        _array_indexing(spec, param, hierarchy_clone, indexed_parameters)

    # Index each element in the object
    elif param['type'] == "object":
        # If there are no properties (undefined schema) and it's not an array, add each type
        if ('properties' not in param) and (not arr):
            param_name = param['name']
            param['name'] = param_name
            param['array'] = arr
            param['hierarchy'] = hierarchy_clone
            indexed_parameters[param_name] = param
            return

        # If there are no properties and not within an array, we should just parse the input as json
        elif 'properties' not in param:
            return []

        # If there are properties or it's within an array, loop through properties and add each.
        # Will be an empty list if it's an array there are no defined properties. In this case,
        # we should parse the input as json.
        object_indexed_params = []
        for (prop_name, payload) in param['properties'].items():
            payload['name'] = prop_name
            payload['req'] = param['req'] and prop_name in param['required']
            payload['in'] = param['in']
            object_indexed_params.append(_recursive_indexing(spec, payload, hierarchy_clone, indexed_parameters, arr))
        return object_indexed_params

    # If this within array, don't set the parameter because we set a parameter value in the array "if"
    elif arr:
        return param

    # Normal type - add it to indexed parameters.
    else:
        param_name = param['name']
        param['name'] = param_name
        param['array'] = arr
        param['hierarchy'] = hierarchy_clone
        indexed_parameters[param_name] = param


def index_parameters(spec, endpoint_info):
    """Map all parameters from parameter name -> parameter info."""
    indexed_parameters = {}
    if 'parameters' in endpoint_info:
        for param in endpoint_info['parameters']:

            # Labelling req instead of required b/c objects have 'required'
            # array to tell which args required. Can't overwrite.
            param['req'] = param.get('required', False)

            # Make sure parameter name is not extras.
            if param['in'] == "body":
                inner_param = param['schema']
                inner_param['in'] = "body"
                inner_param['name'] = "irrelevant"
                inner_param['req'] = param['req']
                param = inner_param

            _recursive_indexing(spec, param, [], indexed_parameters)
    return indexed_parameters


def create_help_statement(endpoint_info):
    """Make the help statement for each command line argument."""
    return endpoint_info['description']


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

    positional = endpoint_params['positional']
    for i in range(max(len(list(path_args)), len(list(positional)))):
        # If this path arg for this base route hasn't been seen, add it to possible args.
        if i >= len(positional):
            argument = path_args[i]
            argrequired = indexed_parameters[argument]['req']
            arg_params = indexed_parameters[argument]
            positional.append({
                'argument': argument,
                'required': argrequired and not endpoint_params['seen'],
                'required_for': [],  # see explanation below
                'description': arg_params.get('description', ""),
                'type': arg_params.get('type', None),
                'format': arg_params.get('format', None),
                'pattern': arg_params.get('pattern', None)
            })
        # If there are more args that weren't seen on this base route, mark then not
        # required because they're not used in every endpoint.
        elif i >= len(path_args):
            positional[i]['required'] = False

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
    options = endpoint_params['options']

    # If in another endpoint with the same base route has a required option that's
    # missing from this endpoint, it's not required.
    for (param_name, param_data) in options.items():
        if param_name not in indexed_parameters:
            param_data['required'] = False

    for (param_name, param_data) in indexed_parameters.items():
        if param_data['in'] != "path":  # Only non-positional args
            argrequired = indexed_parameters[param_name]['req']
            if param_name not in options:
                arg_params = indexed_parameters[param_name]
                options[param_name] = {
                    'array': param_data['array'],
                    'required': argrequired and not endpoint_params['seen'],
                    'required_for': [],
                    'description': arg_params.get('description', ""),
                    'type': arg_params.get('type', None),
                    'format': arg_params.get('format', None),
                    'pattern': arg_params.get('pattern', None),
                    'metavar': arg_params.get('metavar', None),
                    'in': arg_params.get('in', None),
                    'hierarchy': arg_params['hierarchy']
                }
            else:
                options[param_name]['required'] = argrequired and options[param_name]['required']

            # If the arg is required on this endpoint, add this endpoint to the list of
            # endpoints for which this arg is needed.
            if argrequired:
                options[param_name]['required_for'].append(path)


def generate_python_bindings(test_api_path=None):
    """
    Generate classes for each endpoint that allow for easy parser integration and api endpoint interaction.

    :param test_api_path: The swagger api specification used to generate parser. If path is None, use base endpoint.
    """
    spec = _get_spec(test_api_path)
    scheme = spec['schemes'][0] if 'schemes' in spec else "https"
    base_url = "{}://{}{}".format(scheme, spec['host'], spec['basePath'])

    param_holders = {}

    for path in spec['paths']:
        path_split = path.split("/")

        for http_method in spec['paths'][path]:
            endpoint_info = spec['paths'][path][http_method]
            endpoint_name = _make_name(http_method, path_split)
            indexed_parameters = index_parameters(spec, endpoint_info)

            # Start tracking params if there's no current store.
            if endpoint_name not in param_holders:
                param_holders[endpoint_name] = {
                    'seen': False,
                    'positional': [],
                    'options': {},
                    'description': endpoint_info.get('description', "placeholder")
                }
            else:
                param_holders[endpoint_name]['seen'] = True

            # Add args to their base_route-indexed param_data object with requirement indications.
            _label_path_args_required(path, param_holders[endpoint_name], indexed_parameters)
            _label_optional_args_required(path, param_holders[endpoint_name], indexed_parameters)

    # Blow away previous files in the autogenerated folder and remake that directory
    dirname = os.path.dirname(__file__)
    autogenerated_path = os.path.join(dirname, "api", "autogenerated")
    if os.path.exists(autogenerated_path):
        shutil.rmtree(autogenerated_path)
    os.mkdir(autogenerated_path)
    open(os.path.join(autogenerated_path, "__init__.py"), 'a').close()

    for (endpoint_name, endpoint_info) in param_holders.items():

        template_loader = FileSystemLoader(searchpath=os.path.join(dirname, "api", "templates"))

        # An environment provides the data necessary to read and parse our templates. Pass in the loader object here.
        template_env = Environment(loader=template_loader)

        # This constant string specifies the template file we will use.
        template_file = "/api.jinja"

        # Read the template file using the environment object.
        template = template_env.get_template(template_file)

        # Specify any input variables to the template as a dictionary.
        template_vars = {'class_name': _separator_to_camel_case(endpoint_name, "-"),
                         'base_url': base_url,
                         'command_name': endpoint_name,
                         'endpoint_info': endpoint_info}

        # Finally, process the template to produce our final text.
        output_text = template.render(template_vars)

        file_name = format(endpoint_name.replace("-", "_")) + ".py"
        file_path = os.path.join(dirname, "api", "autogenerated", file_name)

        with open(file_path, "w") as f:
            f.write(output_text)


if __name__ == "__main__":
    generate_python_bindings()
