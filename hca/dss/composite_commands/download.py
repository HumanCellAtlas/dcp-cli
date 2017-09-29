from __future__ import absolute_import, division, print_function, unicode_literals

import os

import hca.dss
from io import open
from .. import infra
from ..added_command import AddedCommand
from ..cli import parse_args


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
        logger = infra.get_logger(Download)
        for file_ in files:

            file_uuid = file_['uuid']
            filename = file_.get("name", file_uuid)

            logger.info("%s", "File {}: Retrieving...".format(filename))

            response = hca.dss.get_files(file_uuid, replica=replica, stream=True)

            try:
                if response.ok:
                    file_path = os.path.join(folder, filename)
                    logger.info("%s", "File {}: GET SUCCEEDED. Writing to disk.".format(filename))
                    with open(file_path, "wb") as fh:
                        # Process taken from
                        # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                fh.write(chunk)
                    logger.info("%s", "File {}: GET SUCCEEDED. Stored at {}.".format(filename, file_path))

                else:
                    logger.error("%s", "File {}: GET FAILED.".format(filename))
                    logger.error("%s", "Response: {}".format(response.text))
            finally:
                response.close()

        return {"completed": True}

    @classmethod
    def _download_bundle(cls, args):
        """Use the python bindings to make a get-bundles request."""
        logger = infra.get_logger(Download)
        bundle_uuid = args["uuid"]
        bundle_name = args.get("name", bundle_uuid)
        replica = args["replica"]

        logger.info("%s", "File {}: Retrieving...".format(bundle_uuid))

        response = hca.dss.get_bundles(bundle_uuid, replica=replica)
        try:
            files = [args]
            folder = ""

            if response.ok:
                files = response.json()["bundle"]["files"]
                folder = bundle_name
                if not os.path.isdir(folder):
                    os.makedirs(folder)
                logger.info("%s", "Bundle {}: GET SUCCEEDED.  {} files to download".format(bundle_uuid, len(files)))

            else:
                logger.error("%s", "Bundle {}: GET FAILED.".format(bundle_uuid))
                logger.error("%s", "Response: {}".format(response.text))
            return files, folder
        finally:
            response.close()

    @classmethod
    def run_from_cli(cls, argparser_args):
        """Run this command using args from the cli. Override this to add higher-level commands."""
        args_dict = parse_args(argparser_args)
        return cls.run(args_dict)

    @classmethod
    def run(cls, args):
        """Download a bundle or file from the blue box to local."""
        files, folder = cls._download_bundle(args)
        status = cls._download_files(files, folder, args["replica"])

        return status
