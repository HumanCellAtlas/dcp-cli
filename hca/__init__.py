from .config import HCAConfig, get_config, logger
from . import dss, upload, auth


def clear_hca_cache(args):
    """Clear the cached HCA API definitions. This can help resolve errors communicating with the API."""
    from hca.util import SwaggerClient
    for swagger_client in SwaggerClient.__subclasses__():
        swagger_client().clear_cache()
