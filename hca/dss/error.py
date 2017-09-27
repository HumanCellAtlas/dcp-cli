class APIException(Exception):
    def __init__(self, *args, **kwargs):
        super(APIException, self).__init__(*args, **kwargs)
