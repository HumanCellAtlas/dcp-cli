import base64
import json

from .exceptions import UploadException


class UploadAreaURN:

    def __init__(self, urn):
        self.urn = urn
        urnbits = urn.split(':')
        assert urnbits[0:3] == ['dcp', 'upl', 'aws'], "URN does not start with 'dcp:upl:aws': %s" % (urn,)
        if len(urnbits) == 5:  # production URN dcp:upl:aws:uuid:creds
            self.deployment_stage = 'prod'
            self.uuid = urnbits[3]
            self.encoded_credentials = urnbits[4]
        elif len(urnbits) == 6:  # non-production URN dcp:upl:aws:stage:uuid:creds
            self.deployment_stage = urnbits[3]
            self.uuid = urnbits[4]
            self.encoded_credentials = urnbits[5]
        else:
            raise UploadException("Bad URN: %s" % (urn,))

    def __repr__(self):
        return ":".join(['dcp', 'upl', 'aws', self.deployment_stage, self.uuid])

    @property
    def credentials(self):
        uppercase_credentials = json.loads(base64.b64decode(self.encoded_credentials).decode('ascii'))
        return {k.lower(): v for k, v in uppercase_credentials.items()}
