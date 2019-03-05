from ..util.exceptions import SwaggerAPIException
from .. import logger


class APIException(SwaggerAPIException):
    def __init__(self, *args, **kwargs):
        super(APIException, self).__init__(*args, **kwargs)
        if self.response:
            if self.response['headers']['AWS-Request-ID']:
                logger.error("%s", "X-AWS-REQUEST-ID: {}".format(self.response['headers']['AWS-Request-ID']))
