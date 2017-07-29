from ...added_command import AddedCommand

class PostSearch(AddedCommand):
    """Class containing info to reach the get endpoint of files."""

    @classmethod
    def _get_base_url(cls):
        return "https://hca-dss.czi.technology/v1"

    @classmethod
    def get_command_name(cls):
        return "post-search"

    @classmethod
    def _get_endpoint_info(cls):
        return {u'function_def_arglist': [], u'body_params': {}, u'positional': [], u'seen': False, u'options': {}, u'description': u'Accepts Elasticsearch JSON query and returns matching bundle identifiers\n'}
