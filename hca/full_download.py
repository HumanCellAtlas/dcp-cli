from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys

from io import open


def eprint(*args, **kwargs):
    """Print to stderr."""
    print(*args, file=sys.stderr, **kwargs)


class FullDownload:
    """Functions needed to create the end-to-end parser and actually run the demo."""

    CONSOLE_ARGUMENT = "download"
    UUID = "uuid"

    @classmethod
    def add_parser(cls, subparsers):
        """Call from parser.py to create the parser to run the demo."""
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
            help="Name you're going to assign to the bundle/file you're downloading."
        )

        subparser.add_argument(
            "--replica",
            help="Which cloud to download from first. One of 'aws', 'gc', or 'azure'.",
            default="aws"
        )

    @classmethod
    def _download_files(cls, files, folder, api, replica):
        """Use the API class to make a put-files request on each of these files."""
        for file in files:

            file_uuid = file[cls.UUID]
            filename = file.get("name", file_uuid)

            eprint("File {}: Retrieving...".format(filename))

            request = [
                "get-files",
                file_uuid,
                "--replica", replica,
            ]

            response = api.make_request(request, stream=True)

            if response.ok:
                eprint("File {}: GET successful. Writing to disk.".format(filename, file_uuid))
                with open(folder + filename, "wb") as fh:
                    fh.write(response.content)
                response.close()
                eprint("File {}: write successful. Stored at {}.".format(filename, folder + filename))

            else:
                eprint("File {}: GET FAILED. This uuid is neither a bundle nor a file.".format(filename))
                eprint(response.text)
                response.close()
                response.raise_for_status()

        return {"completed": True}

    @classmethod
    def _download_bundle(cls, args, api):
        """Use the API class to make a get-bundles request."""
        bundle_uuid = args["uuid"]
        bundle_name = args.get("name", bundle_uuid)
        replica = args["replica"]

        eprint("Bundle {}: Retrieving...".format(bundle_uuid))
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
            folder = bundle_name + "/"
            if not os.path.isdir(folder):
                os.mkdir(folder)
            eprint("Bundle {}: GET successful. {} files to download".format(bundle_uuid, len(files)))

        else:
            eprint("Bundle {}: GET FAILED. Checking if uuid is a file.".format(bundle_uuid))
            eprint(response.text)
            response.close()
            response.raise_for_status()

        eprint("Request response:")
        eprint("{}\n".format(response.content.decode()))
        return files, folder

    @classmethod
    def run(cls, args, api):
        """Run through full demo functionality."""
        files, folder = cls._download_bundle(args, api)
        status = cls._download_files(files, folder, api, args["replica"])

        return status
