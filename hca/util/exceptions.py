import json

from requests.exceptions import HTTPError

class SwaggerAPIException(HTTPError):
    """
    Exception raised by SwaggerClient when an HTTP error is received from a Swagger API server.
    """
    def __init__(self, *args, **kwargs):
        super(SwaggerAPIException, self).__init__(*args, **kwargs)

        self.code = self.response.status_code
        self.reason = self.response.reason
        self.details = None
        if self.response.content:
            try:
                self.details = self.response.json()
            except Exception:
                self.details = self.response.text

    def __str__(self):
        if self.details:
            return "{}, code {}. Details:\n{}".format(self.reason, self.code, self.response.text)
        else:
            return "{}, code {}".format(self.response.reason, self.response.status_code)
