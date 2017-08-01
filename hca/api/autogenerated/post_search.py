from ...added_command import AddedCommand

class PostSearch(AddedCommand):
    """Class containing info to reach the get endpoint of files."""

    @classmethod
    def _get_base_url(cls):
        return "https://hca-dss.czi.technology/v1"

    @classmethod
    def _get_endpoint_info(cls):
        return {u'positional': [], u'seen': False, u'options': {}, u'body_params': {}, u'description': u'Accepts Elasticsearch JSON query and returns matching bundle identifiers\n'}
