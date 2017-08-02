from __future__ import absolute_import, division, print_function, unicode_literals

import os
import logging

from io import open
from . import get_bundles, get_files
from ...added_command import AddedCommand


class Download(AddedCommand):
    """Functions needed to fully add this functionality to the command line parser."""

    @classmethod
    def _get_endpoint_info(cls):
        return {
            'body_params': {},
            'description': "Download a full bundle or file to local.",
            'positional': [{
                'argument': "uuid",
                'required': True,
                'type': "string",  # See AddedCommand._get_arg_type() for expected args
                'description': "UUID of the folder or file you want to download."
            }],
            'options': {
                'name': {
                    'description': ("Name of the folder you're storing the bundle/file in (Your name for the bundle)."
                                    " Defaults to the uuid of the bundle or file."),
                    'type': "string",
                    'metavar': None,
                    'required': False,
                    'array': False
                },
                'replica': {
                    'description': "Which cloud to download from first. One of 'aws', 'gcp', or 'azure'.",
                    'type': "string",
                    'metavar': None,
                    'required': False,
                    'array': False,
                    'default': "aws",
                }
            }
        }

    @classmethod
    def _download_files(cls, files, folder, replica):
        """Use the python bindings to make a get-files request on each of these files."""
        for file_ in files:

            file_uuid = file_['uuid']
            filename = file_.get("name", file_uuid)

            logging.info("File {}: Retrieving...".format(filename))

            response = get_files(file_uuid, replica=replica, stream=True)

            if response.ok:
                file_path = os.path.join(folder, filename)
                logging.info("File {}: GET SUCCEEDED. Writing to disk.".format(filename, file_uuid))
                with open(file_path, "wb") as fh:
                    # Process taken from
                    # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            fh.write(chunk)
                response.close()
                logging.info("File {}: GET SUCCEEDED. Stored at {}.".format(filename, file_path))

            else:
                logging.info("File {}: GET FAILED. This uuid is neither a bundle nor a file.".format(filename))
                logging.info(response.text)
                response.close()

        return {"completed": True}

    @classmethod
    def _download_bundle(cls, args):
        """Use the python bindings to make a get-bundles request."""
        bundle_uuid = args["uuid"]
        bundle_name = args.get("name", bundle_uuid)
        replica = args["replica"]

        logging.info("Bundle {}: Retrieving...".format(bundle_uuid))

        response = get_bundles(bundle_uuid, replica=replica)

        files = [args]
        folder = ""

        if response.ok:
            files = response.json()["bundle"]["files"]
            folder = bundle_name
            if not os.path.isdir(folder):
                os.makedirs(folder)
                logging.info("Bundle {}: GET SUCCEEDED. {} files to download".format(bundle_uuid, len(files)))
            logging.info("Request response:")
            logging.info("{}\n".format(response.content.decode()))

        else:
            logging.info("Bundle {}: GET FAILED. Checking if uuid is a file.".format(bundle_uuid))
            logging.info(response.text)
        return files, folder

    @classmethod
    def run_cli(cls, args):
        """Download a bundle/file from blue box to local with arguments given from cli."""
        return cls.run(args)

    @classmethod
    def run(cls, args):
        """Download a bundle or file from the blue box to local."""
        files, folder = cls._download_bundle(args)
        status = cls._download_files(files, folder, args["replica"])

        return status
