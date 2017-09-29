import re

from .config_store import ConfigStore
from .staging_area_urn import StagingAreaURN


class SelectCommand:

    @classmethod
    def add_parser(cls, staging_subparsers):
        select_parser = staging_subparsers.add_parser(
            'select',
            description="Select staging area to which you wish to upload files."
        )
        select_parser.add_argument('urn_or_alias',
                                   help="Full URN of a staging area, or short alias.")
        select_parser.set_defaults(func=SelectCommand)

    def __init__(self, args):
        self.config = ConfigStore()
        if args.urn_or_alias.find(':') == -1:  # alias
            self._select_area_by_alias(args.urn_or_alias)
        else:  # URN
            self._save_and_select_area_by_urn(args.urn_or_alias)
        self.config.save()

    def _save_and_select_area_by_urn(self, urn_string):
        urn = StagingAreaURN(urn_string)
        self.config.add_area(urn)
        self._select_area(urn.uuid)

    def _select_area_by_alias(self, alias):
        matching_areas = self._areas_matching_alias(alias)
        if len(matching_areas) == 0:
            print("Sorry I don't recognize area \"%s\"" % (alias,))
        elif len(matching_areas) == 1:
            self._select_area(matching_areas[0])
        else:
            print("\"%s\" matches more than one area, please provide more characters." % (alias,))

    def _areas_matching_alias(self, alias):
        return [uuid for uuid in self.config.areas() if re.match(alias, uuid)]

    def _select_area(self, area_uuid):
        self.config.select_area(area_uuid)
        print("Staging area %s selected." % area_uuid)
        alias = self._find_unique_prefix(area_uuid)
        print("In future you may refer to this staging area using the alias \"%s\"" % (alias,))

    def _find_unique_prefix(self, area_uuid):
        for prefix_len in range(1, len(area_uuid)):
            prefix = area_uuid[0:prefix_len]
            matches = self._areas_matching_alias(prefix)
            if len(matches) == 1:
                return prefix
