from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import logging

from io import open


class FullDownload:
    """Functions needed to fully add this functionality to the command line parser."""

    CONSOLE_ARGUMENT = "download"
    UUID = "uuid"

    @classmethod
    def add_parser(cls, subparsers):
        """Call from parser.py to create the parser."""
        subparser = subparsers.add_parser(
            cls.CONSOLE_ARGUMENT,
            help="Download a full bundle or file to local."
        )

        subparser.add_argument(
            cls.UUID,
            help="UUID of the folder or file you want to download."
        )

        subparser.add_argument(
            "--name",
            help="Name of the folder you're storing the bundle/file in (Your name for the bundle).\
                Defaults to the uuid of the bundle or file."
        )

        subparser.add_argument(
            "--replica",
            help="Which cloud to download from first. One of 'aws', 'gcp', or 'azure'.",
            choices=['aws', 'gcp', 'azure'],
            default="aws"
        )

    @classmethod
    def _download_files(cls, files, folder, api, replica):
        """Use the API class to make a get-files request on each of these files."""
        for file_ in files:

            file_uuid = file_[cls.UUID]
            filename = file_.get("name", file_uuid)

            logging.info("File {}: Retrieving...".format(filename))

            request = [
                "get-files",
                file_uuid,
                "--replica", replica,
            ]

            response = api.make_request(request, stream=True)

            if response.ok:
                file_path = os.path.join(folder, filename)
                logging.info("File {}: GET successful. Writing to disk.".format(filename, file_uuid))
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
    def _download_bundle(cls, args, api):
        """Use the API class to make a get-bundles request."""
        bundle_uuid = args["uuid"]
        bundle_name = args.get("name", bundle_uuid)
        replica = args["replica"]

        logging.info("Bundle {}: Retrieving...".format(bundle_uuid))
        request = [
            "get-bundles",
            bundle_uuid,
            "--replica", replica,
        ]

        files = [args]
        folder = ""
        response = api.make_request(request)

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
    def run(cls, args, api):
        """Download a bundle or file from the blue box to local."""
        files, folder = cls._download_bundle(args, api)
        status = cls._download_files(files, folder, api, args["replica"])

        return status
