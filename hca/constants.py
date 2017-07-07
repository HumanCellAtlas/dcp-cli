"""File to keep constants together."""

from __future__ import absolute_import, division, print_function, unicode_literals


class Constants:
    """Class to keep constants together."""

    # The character to split the variables within an object when they're listed.
    # In the put-bundles command, the files should be specified as <V1><OBJECT_SPLITTER><V2><OBJECT_SPLITTER><V3>...
    OBJECT_SPLITTER = "/"
