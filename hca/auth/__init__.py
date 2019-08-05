"""
Authorization and Authentication system
***************************************
"""

from __future__ import absolute_import, division, print_function, unicode_literals


from ..util import SwaggerClient


class AuthClient(SwaggerClient):
    """
    Client for Authentication and Authorization System.
    """

    def __init__(self, *args, **kwargs):
        super(AuthClient, self).__init__(*args, **kwargs)
        self.commands += []

