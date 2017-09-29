class StagingAreaURN:

    def __init__(self, urn):
        self.urn = urn
        urnbits = urn.split(':')
        assert urnbits[0:3] == ['hca', 'sta', 'aws'], "URN does not start with 'hca:sta:aws': %s" % (urn,)
        if len(urnbits) == 5:  # production URN hca:sta:aws:uuid:creds
            self.uuid = urnbits[3]
        elif len(urnbits) == 6:  # non-production URN hca:sta:aws:stage:uuid:creds
            self.uuid = urnbits[4]
        else:
            raise RuntimeError("Bad URN: %s" % (urn,))
