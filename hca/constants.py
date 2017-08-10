"""File to keep constants together."""

from __future__ import absolute_import, division, print_function, unicode_literals


class Constants:
    """Class to keep constants together."""

    # List of all higher-level command classes that do more than provide baseline interaction with api.
    # In regenerate_api.py, when looping through classes in the composite_commands module, the classes
    # that are imported are included too. To ensure those aren't imported, explicitly state which classes
    # to import and generate python bindings/cli commands for.
    composite_commands_class_names = ["Upload", "Download"]

    # The character to split the variables within an object when they're listed.
    # In the put-bundles command, the files should be specified as <V1><OBJECT_SPLITTER><V2><OBJECT_SPLITTER><V3>...
    OBJECT_SPLITTER = "/"
