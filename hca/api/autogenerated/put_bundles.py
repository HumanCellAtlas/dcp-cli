"""This file is autogenerated according to HCA api spec. DON'T TOUCH!"""
from ...added_command import AddedCommand

class PutBundles(AddedCommand):
    """Class containing info to reach the get endpoint of files."""

    @classmethod
    def _get_base_url(cls):
        return "https://hca-dss.czi.technology/v1"

    @classmethod
    def _get_endpoint_info(cls):
        return {u'positional': [{u'description': u'A RFC4122-compliant ID for the bundle.', u'format': None, u'pattern': u'[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}', u'required': True, u'argument': u'uuid', u'required_for': [u'/bundles/{uuid}'], u'type': u'string'}], u'seen': False, u'options': {u'files': {u'hierarchy': [u'files', [(u'indexed', u'boolean'), (u'name', u'string'), (u'uuid', u'string'), (u'version', u'string')]], u'in': u'body', u'description': u'\nindexed: True iff this file should be indexed.\nname: Name of the file.\nuuid: A RFC4122-compliant ID for the file.\nversion: Timestamp of file creation in RFC3339.', u'required_for': [u'/bundles/{uuid}'], u'format': None, u'pattern': None, u'array': True, u'required': True, u'type': u'string', u'metavar': u'INDEXED/NAME/UUID/VERSION'}, u'creator_uid': {u'hierarchy': [u'creator_uid'], u'in': u'body', u'description': u'User ID who is creating this bundle.', u'required_for': [u'/bundles/{uuid}'], u'format': u'int64', u'pattern': None, u'array': False, u'required': True, u'type': u'integer', u'metavar': None}, u'version': {u'hierarchy': [u'version'], u'in': u'query', u'description': u'Timestamp of bundle creation in RFC3339.', u'required_for': [], u'format': u'date-time', u'pattern': None, u'array': False, u'required': False, u'type': u'string', u'metavar': None}, u'replica': {u'hierarchy': [u'replica'], u'in': u'query', u'description': u'Replica to write to.', u'required_for': [u'/bundles/{uuid}'], u'format': None, u'pattern': None, u'array': False, u'required': True, u'type': u'string', u'metavar': None}}, u'body_params': {u'files': {u'items': {u'required': [u'uuid', u'version', u'name', u'indexed'], u'name': u'files', u'req': True, u'in': u'body', u'type': u'object', u'properties': {u'indexed': {u'req': True, u'type': u'boolean', u'description': u'True iff this file should be indexed.', u'in': u'body', u'name': u'indexed'}, u'version': {u'description': u'Timestamp of file creation in RFC3339.', u'format': u'date-time', u'req': True, u'in': u'body', u'type': u'string', u'name': u'version'}, u'name': {u'description': u'Name of the file.', u'pattern': u'^[^/\\\\]+$', u'req': True, u'in': u'body', u'type': u'string', u'name': u'name'}, u'uuid': {u'description': u'A RFC4122-compliant ID for the file.', u'pattern': u'[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}', u'req': True, u'in': u'body', u'type': u'string', u'name': u'uuid'}}}, u'req': True, u'type': u'array', u'name': u'files', u'in': u'body'}, u'creator_uid': {u'description': u'User ID who is creating this bundle.', u'format': u'int64', u'hierarchy': [u'creator_uid'], u'req': True, u'in': u'body', u'array': False, u'type': u'integer', u'name': u'creator_uid'}}, u'description': u'Create a new version of a bundle with a given UUID.  The list of file UUID+versions to be included must be\nprovided.\n'}
