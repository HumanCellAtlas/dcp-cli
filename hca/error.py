class APIException(Exception):
    def __init__(self, *args, **kwargs):
        super(APIException, self).__init__(*args, **kwargs)


class PrintingException(Exception):
    """NonPrintingParser will raise this to notify CLI to exit and transfer help message (needed for slackbot)."""

    def __init__(self, *args, **kwargs):
        super(PrintingException, self).__init__(*args, **kwargs)
