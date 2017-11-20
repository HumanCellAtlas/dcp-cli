"""
This file contains utility functions for the DCP CLI.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, types, collections, typing, json, errno, base64, argparse

try:
    from inspect import signature, Signature, Parameter
except ImportError:
    from funcsigs import signature, Signature, Parameter

import requests
from requests_oauthlib import OAuth2Session

from .. import get_config, logger
from .compat import USING_PYTHON2
from .exceptions import SwaggerAPIException
from ._docs import _pagination_docstring, _streaming_docstring, _md2rst

class _ClientMethodFactory(object):
    def __init__(self, client, parameters, path_parameters, http_method, method_name, method_data, body_props):
        self.__dict__.update(locals())
        self._context_manager_response = None

    def _request(self, req_args, url=None, stream=False):
        supplied_path_params = [p for p in req_args if p in self.path_parameters and req_args[p] is not None]
        if url is None:
            url = self.client.host + self.client.http_paths[self.method_name][frozenset(supplied_path_params)]
            url = url.format(**req_args)
        logger.debug("%s %s %s", self.http_method, url, req_args)
        query = {k: v for k, v in req_args.items()
                 if self.parameters.get(k, {}).get("in") == "query" and v is not None}
        body = {k: v for k, v in req_args.items() if k in self.body_props and v is not None}
        if "security" in self.method_data:
            session = self.client.get_authenticated_session()
        else:
            session = self.client.get_session()

        # TODO: (akislyuk) if using service account credentials, use manual refresh here
        json_input = body if self.body_props else None
        res = session.request(self.http_method, url, params=query, json=json_input, stream=stream)
        if res.status_code >= 400:
            raise SwaggerAPIException(response=res)
        return res

    def _consume_response(self, response):
        if self.http_method.upper() == "HEAD":
            return response
        elif response.headers["content-type"].startswith("application/json"):
            return response.json()
        else:
            return response.content

    def __call__(self, client, **kwargs):
        return self._consume_response(self._request(kwargs))

    def _cli_call(self, cli_args):
        return self._consume_response(self._request(vars(cli_args)))

    def stream(self, **kwargs):
        self._context_manager_response = self._request(kwargs, stream=True)
        return self

    def __enter__(self, **kwargs):
        assert self._context_manager_response is not None
        return self._context_manager_response

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context_manager_response.close()
        self._context_manager_response = None

class _PaginatingClientMethodFactory(_ClientMethodFactory):
    def iterate(self, **kwargs):
        page = None
        while page is None or page.links.get("next", {}).get("url"):
            page = self._request(kwargs, url=page.links["next"]["url"] if page else None)
            for result in page.json()["results"]:
                    yield result


class SwaggerClient(object):
    scheme = "https"
    _authenticated_session = None
    _session = None
    _swagger_spec = None
    _type_map = {
        "string": str,
        "number": float,
        "integer": int,
        "boolean": bool,
        "array": typing.List,
        "object": typing.Mapping
    }
    def __init__(self, config=None, **session_kwargs):
        self.config = config or get_config()
        self._session_kwargs = session_kwargs

        if USING_PYTHON2:
            self.__doc__ = _md2rst(self.swagger_spec["info"]["description"])
        else:
            self.__class__.__doc__ = _md2rst(self.swagger_spec["info"]["description"])
        self.methods = {}
        self.commands = [self.login, self.logout]
        self.http_paths = collections.defaultdict(dict)
        self.host = "{scheme}://{host}{base}".format(scheme=self.scheme,
                                                     host=self.swagger_spec["host"],
                                                     base=self.swagger_spec["basePath"])
        for http_path, path_data in self.swagger_spec["paths"].items():
            for http_method, method_data in path_data.items():
                self._build_client_method(http_method, http_path, method_data)

    @property
    def swagger_spec(self):
        if not self._swagger_spec:
            if "swagger_filename" in self.config:
                swagger_filename = self.config.swagger_filename
                if not swagger_filename.startswith("/"):
                    swagger_filename = os.path.join(os.path.dirname(__file__), swagger_filename)
            else:
                swagger_filename = base64.urlsafe_b64encode(self.config.swagger_url.encode()).decode() + ".json"
                swagger_filename = os.path.join(self.config.user_config_dir, swagger_filename)
            if not os.path.exists(swagger_filename):
                try:
                    os.makedirs(self.config.user_config_dir)
                except OSError as e:
                    if not (e.errno == errno.EEXIST and os.path.isdir(self.config.user_config_dir)):
                        raise
                with open(swagger_filename, "wb") as fh:
                    fh.write(requests.get(self.config.swagger_url).content)
            with open(swagger_filename) as fh:
                self.__class__._swagger_spec = json.load(fh)
        return self._swagger_spec

    @property
    def application_secrets(self):
        if "application_secrets" not in self.config:
            app_secrets_url = "https://{}/internal/application_secrets".format(self._swagger_spec["host"])
            self.config.application_secrets = requests.get(app_secrets_url).json()
        return self.config.application_secrets

    def get_session(self):
        if self._session is None:
            self._session = requests.Session(**self._session_kwargs)
            self._session.headers.update({"User-Agent": self.__class__.__name__})
        return self._session

    def logout(self):
        """
        Clear {prog} authentication credentials previously configured with ``{prog} login``.
        """
        try:
            del self.config["oauth2_token"]
        except KeyError:
            pass

    def login(self, access_token=""):
        """
        Configure and save {prog} authentication credentials.

        This command may open a browser window to ask for your
        consent to use web service authentication credentials.
        """
        if access_token:
            credentials = argparse.Namespace(token=access_token, refresh_token=None, id_token=None)
        else:
            scopes = ["https://www.googleapis.com/auth/userinfo.email"]
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_config(self.application_secrets, scopes=scopes)
            credentials = flow.run_local_server()
        # TODO: (akislyuk) test token autorefresh on expiration
        self.config.oauth2_token = dict(access_token=credentials.token,
                                        refresh_token=credentials.refresh_token,
                                        id_token=credentials.id_token,
                                        expires_at="-1",
                                        token_type="Bearer")
        print("Storing access credentials")

    def _get_oauth_token_from_service_account_credentials(self):
        scopes = ["https://www.googleapis.com/auth/userinfo.email"]
        assert 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ
        from google.auth.transport.requests import Request as GoogleAuthRequest
        from google.oauth2.service_account import Credentials as ServiceAccountCredentials
        logger.info("Found GOOGLE_APPLICATION_CREDENTIALS environment variable. "
                    "Using service account credentials for authentication.")
        service_account_credentials_filename = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

        if not os.path.isfile(service_account_credentials_filename):
            msg = 'File "{}" referenced by the GOOGLE_APPLICATION_CREDENTIALS environment variable does not exist'
            raise Exception(msg.format(service_account_credentials_filename))

        credentials = ServiceAccountCredentials.from_service_account_file(
            service_account_credentials_filename,
            scopes=scopes
        )
        r = GoogleAuthRequest()
        credentials.refresh(r)
        r.session.close()
        return credentials.token, credentials.expiry

    def get_authenticated_session(self):
        if self._authenticated_session is None:
            oauth2_client_data = self.application_secrets["installed"]
            if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                token, expires_at = self._get_oauth_token_from_service_account_credentials()
                # TODO: (akislyuk) figure out the right strategy for persisting the service account oauth2 token
                self._authenticated_session = OAuth2Session(client_id=oauth2_client_data["client_id"],
                                                            token=dict(access_token=token),
                                                            **self._session_kwargs)
            else:
                if "oauth2_token" not in self.config:
                    raise Exception('Please configure {prog} authentication credentials using "{prog} login" '
                                    'or set the GOOGLE_APPLICATION_CREDENTIALS environment variable')
                self._authenticated_session = OAuth2Session(
                    client_id=oauth2_client_data["client_id"],
                    token=self.config.oauth2_token,
                    auto_refresh_url=oauth2_client_data["token_uri"],
                    auto_refresh_kwargs=dict(client_id=oauth2_client_data["client_id"],
                                             client_secret=oauth2_client_data["client_secret"]),
                    token_updater=self._save_auth_token_refresh_result,
                    **self._session_kwargs
                )
            self._authenticated_session.headers.update({"User-Agent": self.__class__.__name__})
        return self._authenticated_session

    def _save_auth_token_refresh_result(self, result):
        self.config.oauth2_token = result

    def _build_client_method(self, http_method, http_path, method_data):
        method_name_parts = [http_method] + [p for p in http_path.split("/")[1:] if not p.startswith("{")]
        method_name = "_".join(method_name_parts)
        if method_name.endswith("s") and (http_method.upper() in {"POST", "PUT"} or http_path.endswith("/{uuid}")):
            method_name = method_name[:-1]

        method_args = collections.OrderedDict()
        parameters = {p["name"]: p for p in method_data["parameters"]}

        path_parameters = [p_name for p_name, p_data in parameters.items() if p_data["in"] == "path"]
        self.http_paths[method_name][frozenset(path_parameters)] = http_path

        body_props = {}
        for parameter in parameters.values():
            if parameter["in"] == "body":
                for prop_name, prop_data in parameter["schema"]["properties"].items():
                    anno = self._type_map[prop_data["type"]]
                    if prop_name not in parameter["schema"]["required"]:
                        anno = typing.Optional[anno]
                    param = Parameter(prop_name, Parameter.POSITIONAL_OR_KEYWORD, default=prop_data.get("default"),
                                      annotation=anno)
                    method_args[prop_name] = dict(param=param, doc=prop_data.get("description"),
                                                  choices=parameter.get("enum"))
                    body_props[prop_name] = parameter["schema"]
            else:
                annotation = str if parameter.get("required") else typing.Optional[str]
                param = Parameter(parameter["name"], Parameter.POSITIONAL_OR_KEYWORD, default=parameter.get("default"),
                                  annotation=annotation)
                method_args[parameter["name"]] = dict(param=param, doc=parameter.get("description"),
                                                      choices=parameter.get("enum"))

        method_supports_pagination = True if str(requests.codes.partial) in method_data["responses"] else False
        highlight_streaming_support = True if str(requests.codes.found) in method_data["responses"] else False

        factory = _PaginatingClientMethodFactory if method_supports_pagination else _ClientMethodFactory
        client_method = factory(self, parameters, path_parameters, http_method, method_name, method_data, body_props)
        client_method.__name__ = method_name
        client_method.__qualname__ = self.__class__.__name__ + "." + method_name

        params = [Parameter("factory", Parameter.POSITIONAL_OR_KEYWORD),
                  Parameter("client", Parameter.POSITIONAL_OR_KEYWORD)]
        params += [v["param"] for k, v in method_args.items() if not k.startswith("_")]
        client_method.__signature__ = signature(client_method).replace(parameters=params)
        docstring = method_data["summary"] + "\n\n"

        if method_supports_pagination:
            docstring += _pagination_docstring.format(client_name=self.__class__.__name__, method_name=method_name)

        if highlight_streaming_support:
            docstring += _streaming_docstring.format(client_name=self.__class__.__name__, method_name=method_name)

        for param in method_args:
            if not param.startswith("_"):
                param_doc = _md2rst(method_args[param]["doc"] or "")
                docstring += ":param {}: {}\n".format(param, param_doc.replace("\n", " "))
                docstring += ":type {}: {}\n".format(param, method_args[param]["param"].annotation)
        docstring += "\n\n" + _md2rst(method_data["description"])
        client_method.__doc__ = docstring

        setattr(self.__class__, method_name, types.MethodType(client_method, SwaggerClient))
        self.methods[method_name] = dict(method_data, entry_point=getattr(self, method_name)._cli_call,
                                         signature=client_method.__signature__, args=method_args)

    def _command_arg_forwarder_factory(self, command, command_sig):
        def arg_forwarder(parsed_args):
            command_args = {k: v for k, v in vars(parsed_args).items() if k in command_sig.parameters}
            return command(**command_args)
        return arg_forwarder

    def _get_command_arg_settings(self, param_data):
        if param_data.default is Parameter.empty:
            return dict(required=True)
        elif isinstance(param_data.default, (list, tuple)):
            return dict(nargs="+", required=True)
        else:
            return dict(type=type(param_data.default))

    def build_argparse_subparsers(self, subparsers):
        for method_name, method_data in self.methods.items():
            subcommand_name = method_name.replace("_", "-")
            subparser = subparsers.add_parser(subcommand_name, help=method_data.get("summary"),
                                              description=method_data.get("description"))
            for param_name, param in method_data["signature"].parameters.items():
                if param_name in {"client", "factory"}:
                    continue
                logger.debug("Registering %s %s %s", method_name, param_name, param.annotation)
                nargs = "+" if param.annotation == typing.List else None
                argparse_type = json.loads if param.annotation in {typing.List, typing.Mapping} else param.annotation
                subparser.add_argument("--" + param_name.replace("_", "-").replace("/", "-"), dest=param_name,
                                       type=argparse_type, nargs=nargs, help=method_data["args"][param_name]["doc"],
                                       choices=method_data["args"][param_name]["choices"])
            subparser.set_defaults(entry_point=method_data["entry_point"])

        for command in self.commands:
            sig = signature(command)
            doc = command.__doc__.strip().format(prog=subparsers._prog_prefix)
            command_subparser = subparsers.add_parser(command.__name__,
                                                      help=doc.splitlines()[0],
                                                      description=doc)
            command_subparser.set_defaults(entry_point=self._command_arg_forwarder_factory(command, sig))
            for param_name, param_data in sig.parameters.items():
                command_subparser.add_argument("--" + param_name.replace("_", "-"),
                                               **self._get_command_arg_settings(param_data))