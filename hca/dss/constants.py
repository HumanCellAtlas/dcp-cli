"""File to keep constants together."""

from __future__ import absolute_import, division, print_function, unicode_literals


class Constants:
    """Class to keep constants together."""

    # List of all higher-level command classes that do more than provide baseline interaction with api.
    # This is used in regenerate_api.py to have a definitive list of composite commands to import.
    composite_commands_class_names = ["Upload", "Download", "Login"]

    # The character to split the variables within an object when they're listed.
    # In the put-bundles command, the files should be specified as <V1><OBJECT_SPLITTER><V2><OBJECT_SPLITTER><V3>...
    OBJECT_SPLITTER = "/"
    APPLICATION_SECRETS_ENDPOINT = "https://dss.staging.data.humancellatlas.org/internal/application_secrets"
    CHUNK_SIZE = (2 ** 20) * 16  # 16 MB
