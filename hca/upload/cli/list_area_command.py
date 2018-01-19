from .. import list_current_area
from .common import UploadCLICommand


class ListAreaCommand(UploadCLICommand):
    """
    List contents of currently selected upload area.
    """
    @classmethod
    def add_parser(cls, staging_subparsers):
        list_area_parser = staging_subparsers.add_parser(
            'list', description=cls.__doc__, help=cls.__doc__)
        list_area_parser.set_defaults(entry_point=ListAreaCommand)
        list_area_parser.add_argument('-l', '--long', action='store_true', help="Long listing - show file details.")

    def __init__(self, args):
        for f in list_current_area(detail=args.long):
            print(f['name'])
            if args.long:
                print("\t%-12s %d bytes\n\t%-12s %s\n\t%-12s %s" % (
                    'size', f['size'],
                    'URL', f['url'],
                    'Content-Type', f['content_type']
                ))
                if 'checksums' in f:
                    for checksum in ('S3_Etag', 'CRC32C', 'SHA1', 'SHA256'):
                        if checksum.lower() in f['checksums']:
                            print("\t%-12s %s" % (checksum, f['checksums'][checksum.lower()]))
