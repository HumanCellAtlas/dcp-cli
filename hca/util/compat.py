from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re
import sys

USING_PYTHON2 = True if sys.version_info < (3, 0) else False

if USING_PYTHON2:
    # https://github.com/python/cpython/blob/master/Lib/glob.py#L142
    _magic_check = re.compile('([*?[])')
    _magic_check_bytes = re.compile(b'([*?[])')

    # https://github.com/python/cpython/blob/master/Lib/glob.py#L161
    def glob_escape(pathname):
        """Escape all special characters.
        """
        # Escaping is done by wrapping any of "*?[" between square brackets.
        # Metacharacters do not work in the drive part and shouldn't be escaped.
        drive, pathname = os.path.splitdrive(pathname)
        if isinstance(pathname, bytes):
            pathname = _magic_check_bytes.sub(br'[\1]', pathname)
        else:
            pathname = _magic_check.sub(r'[\1]', pathname)
        return drive + pathname
else:
    from glob import escape as glob_escape

if sys.version_info < (3, 5):
    from scandir import scandir, walk
else:
    from os import scandir, walk

__all__ = ('USING_PYTHON2', 'glob_escape', 'scandir', 'walk')
