from requests.exceptions import HTTPError

class SwaggerAPIException(HTTPError):
    """
    Exception raised by SwaggerClient when an HTTP error is received from a Swagger API server.
    """
    def __init__(self, *args, **kwargs):
        super(SwaggerAPIException, self).__init__(*args, **kwargs)

        self.code = self.response.status_code
        self.reason = self.response.reason
        self.details, self.title, self.stacktrace = None, None, None
        if self.response.content:
            try:
                self.details = self.response.json()
                self.reason = self.details.get("code")
                self.title = self.details.get("title")
                self.stacktrace = self.details.get("stacktrace")
            except Exception:
                self.details = self.response.text

    def __str__(self):
        if self.details:
            if self.stacktrace:
                return "{}: {} (HTTP {}). Details:\n{}".format(self.reason, self.title, self.code, self.stacktrace)
            return "{}: {} (HTTP {}). Details:\n{}".format(self.reason, self.title, self.code, self.response.text)
        return "{}, code {}".format(self.response.reason, self.response.status_code)

class SwaggerClientInternalError(Exception):
    pass
