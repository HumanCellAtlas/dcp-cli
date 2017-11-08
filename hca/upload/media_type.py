import operator
import os
import re

import puremagic


class MediaType:

    DCP_METADATA_JSON_FILES = ('assay', 'project', 'sample')
    RFC7320_TOKEN_CHARSET = r"!#$%&'*+\-.^_`|~\w"
    _TYPE_REGEX = re.compile(
        r"(?P<top_level_type>.+)"  # 'application'
        r"/"                       # '/'
        r"(?P<subtype>[^+]+)"      # 'json'
        r"("                       # stat of suffix group
        r"\+(?P<suffix>.+)"        # '+zip'
        r")?"                      # end optional suffix group
    )
    _PARAM_REGEX = re.compile(
        r"\s*"                               # optional whitespace
        r"(?P<key>"                          # start of group 'key'
        r"[" + RFC7320_TOKEN_CHARSET + "]+"  # key
        r")"                                 # end of group 'key'
        r"\s*=\s*"                           # '='
        r"(?P<value>"                        # start of group 'value'
        r'"(?:[^\\"]|\\.)*"'                 # Any doublequoted string
        r"|"                                 # or
        "[" + RFC7320_TOKEN_CHARSET + "]*"   # A word of token-chars (doesn't need quoting)
        r")"                                 # end of group 'value'
        r"\s*(;|$)"                          # Ending either at semicolon, or EOS.
    )
    _QUOTED_PAIR_REGEX = re.compile(r"[\\].")

    @classmethod
    def from_string(cls, media_type):
        first_semi_position = media_type.find(';')
        if first_semi_position == -1:
            type_info = media_type
            parameters = {}
        else:
            type_info = media_type[0:first_semi_position]
            parameters = MediaType._parse_parameters(media_type[first_semi_position + 1:])

        type_info = MediaType._TYPE_REGEX.match(type_info)

        return cls(
            type_info.group('top_level_type'), type_info.group('subtype'),
            suffix=type_info.group('suffix'), parameters=parameters)

    @staticmethod
    def _parse_parameters(params_string):
        parameters = {}
        cursor = 0
        string_length = len(params_string)

        while 0 <= cursor < string_length:
            match = MediaType._PARAM_REGEX.match(params_string, cursor)
            if not match:
                break
            value = match.group('value')
            parameters[match.group('key')] = MediaType._unquote(value)
            cursor = match.end(0)
        return parameters

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
            maintype += "+" + self.suffix
        return maintype

    @staticmethod
    def _media_type_from_magic(file_path):
        """
        Use puremagic to generate a media-type for the file, then correct its mistakes.
        """
        types = puremagic.magic_file(file_path)
        if len(types) == 0:
            return 'application/octet-stream'
        media_type = types[0][1]
        if media_type == 'application/x-ipynb+json':  # All JSON files are not Jupiter notebooks
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
            return MediaType._quote(value)

    _Translator = {
        '"': '\\"',
        '\\': '\\\\'
    }

    @staticmethod
    def _quote(string):
        """
        https://tools.ietf.org/html/rfc7230#section-3.2.6

        The backslash octet ("\") can be used as a single-octet quoting
        mechanism within quoted-string and comment constructs.  Recipients
        that process the value of a quoted-string MUST handle a quoted-pair
        as if it were replaced by the octet following the backslash.

          quoted-pair    = "\" ( HTAB / SP / VCHAR / obs-text )

        A sender SHOULD NOT generate a quoted-pair in a quoted-string except
        where necessary to quote DQUOTE and backslash octets occurring within
        that string.
        """
        return '"' + ''.join(map(MediaType._Translator.get, string, string)) + '"'

    @staticmethod
    def _unquote(string):
        # If there aren't any doublequotes, then there can't be any special characters.
        if len(string) < 2:
            return string
        if string[0] != '"' or string[-1] != '"':
            return string

        string = string[1:-1]  # Remove the "s

        # Check for special sequences.  Examples:
        #    \"   --> "
        cursor = 0
        strlen = len(string)
        result = []
        while 0 <= cursor < strlen:
            match = MediaType._QUOTED_PAIR_REGEX.search(string, cursor)
            if match:
                backslash_location = match.start(0)
                result.append(string[cursor:backslash_location])
                result.append(string[backslash_location + 1])
                cursor = backslash_location + 2
            else:
                result.append(string[cursor:])
                break

        return ''.join(result)
