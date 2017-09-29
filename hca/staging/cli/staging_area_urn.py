import base64
import json


class StagingAreaURN:

    def __init__(self, urn):
        self.urn = urn
        urnbits = urn.split(':')
        assert urnbits[0:3] == ['hca', 'sta', 'aws'], "URN does not start with 'hca:sta:aws': %s" % (urn,)
        if len(urnbits) == 5:  # production URN hca:sta:aws:uuid:creds
            self.deployment_stage = 'prod'
            self.uuid = urnbits[3]
            self.encoded_credentials = urnbits[4]
        elif len(urnbits) == 6:  # non-production URN hca:sta:aws:stage:uuid:creds
            self.deployment_stage = urnbits[3]
            self.uuid = urnbits[4]
            self.encoded_credentials = urnbits[5]
        else:
            raise RuntimeError("Bad URN: %s" % (urn,))

    def credentials(self):
        uppercase_credentials = json.loads(base64.b64decode(self.encoded_credentials).decode('ascii'))
        return {k.lower(): v for k, v in uppercase_credentials.items()}
