"""
HCA DCP CLI!
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, logging

from .define_api import Api

def main():
    api = Api("a", "b", "c")
    print("Hello HCA! :)")
    return api.make_request(sys.argv[1:])
