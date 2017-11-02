import magic
import operator
import os
import re


class MediaType:

    RFC7320_TOKEN_CHARSET = "!#$%&'*+-.^_`|~\w"
    DCP_METADATA_JSON_FILES = ('assay', 'project', 'sample')

    @classmethod
    def from_string(cls, media_type):
        split_on_semicolons = media_type.split(';')
        type_info = split_on_semicolons.pop(0)
        type_info = re.match("(?P<top_level_type>.+)/(?P<subtype>[^+]+)(?P<suffix>\+.+)?", type_info)
        parameters = {}
        for parameter in split_on_semicolons:
            param_match = re.match('(.+)=(.+)', parameter.strip())
            parameters[param_match.group(1)] = param_match.group(2).strip('"')
        return cls(
            type_info.group('top_level_type'), type_info.group('subtype'),
            suffix=type_info.group('suffix'), parameters=parameters)

    @classmethod
    def from_file(cls, file_path, dcp_type=None):
        media_type_string = cls._media_type_from_magic(file_path)
        media_type = cls.from_string(media_type_string)
        if dcp_type:
            media_type.parameters['dcp-type'] = dcp_type
        else:
            media_type.parameters['dcp-type'] = cls._dcp_media_type_param(media_type, os.path.basename(file_path))
        return media_type

    def __init__(self, top_level_type, subtype, suffix=None, parameters={}):
        self.top_level_type = top_level_type
        self.subtype = subtype
        self.suffix = suffix
        self.parameters = parameters

    def __str__(self):
        result = [self.main_type]
        if self.parameters:
            sorted_params = sorted(self.parameters.items(), key=operator.itemgetter(0))
            for k, v in sorted_params:
                result.append('{key}={value}'.format(key=k, value=self._properly_quoted_parameter_value(v)))
        return '; '.join(result)

    @property
    def main_type(self):
        maintype = "{type}/{subtype}".format(type=self.top_level_type, subtype=self.subtype)
        if self.suffix:
            maintype += self.suffix
        return maintype

    @staticmethod
    def _media_type_from_magic(file_path):
        """
        Use libmagic to generate a media-type for the file, then correct its mistakes.
        """
        media_type = magic.from_file(file_path, mime=True)
        if media_type == 'text/plain':  # libmagic doesn't recognize JSON
            if file_path.endswith('.json'):
                media_type = 'application/json'
        elif media_type == 'application/x-gzip':  # deprecated
            media_type = 'application/gzip'
        return media_type

    @staticmethod
    def _dcp_media_type_param(media_type, filename):
        if media_type.main_type == 'application/json':
            (filename_without_extension, ext) = os.path.splitext(filename)
            if filename_without_extension in MediaType.DCP_METADATA_JSON_FILES:
                return "metadata/{filename}".format(filename=filename_without_extension)
            else:
                return "metadata"
        else:
            return "data"

    @staticmethod
    def _properly_quoted_parameter_value(value):
        """
        Per RFC 7321 (https://tools.ietf.org/html/rfc7231#section-3.1.1.1):
        Parameters values don't need to be quoted if they are a "token".
        Token characters are defined by RFC 7320 (https://tools.ietf.org/html/rfc7230#section-3.2.6).
        Otherwise, parameters values can be a "quoted-string".
        So we will quote values that contain characters other than the standard token characters.
        """
        if re.match("^[{charset}]*$".format(charset=MediaType.RFC7320_TOKEN_CHARSET), value):
            return value
        else:
            return '"{}"'.format(value)
