from .. import list_current_area


class ListAreaCommand:

    @classmethod
    def add_parser(cls, staging_subparsers):
        list_area_parser = staging_subparsers.add_parser(
            'list', description="List contents of currently selected upload area.")
        list_area_parser.set_defaults(func=ListAreaCommand)
        list_area_parser.add_argument('-l', '--long', action='store_true', help="Long listing - show file details.")

    def __init__(self, args):
        files = list_current_area()
        for f in files:
            print(f['name'])
            if args.long:
                print("\t%-12s %d bytes\n\t%-12s %s\n\t%-12s %s" % (
                    'size', f['size'],
                    'URL', f['url'],
                    'Content-Type', f['content_type']
                ))
                if 'checksums' in f:
                    for checksum in ('S3_Etag', 'CEC32C', 'SHA1', 'SHA256'):
                        if checksum.lower() in f['checksums']:
                            print("\t%-12s %s" % (checksum, f['checksums'][checksum.lower()]))
