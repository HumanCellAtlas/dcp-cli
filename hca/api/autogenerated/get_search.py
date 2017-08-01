from ...added_command import AddedCommand

class GetSearch(AddedCommand):
    """Class containing info to reach the get endpoint of files."""

    @classmethod
    def _get_base_url(cls):
        return "https://hca-dss.czi.technology/v1"

    @classmethod
    def _get_endpoint_info(cls):
        return {u'positional': [], u'seen': False, u'options': {u'query': {u'hierarchy': [u'query'], u'in': u'query', u'description': u'Metadata query', u'required_for': [u'/search'], u'format': None, u'pattern': None, u'array': False, u'required': True, u'type': u'string', u'metavar': None}}, u'body_params': {}, u'description': u'Returns a list of bundles matching the given simple criteria\n'}
