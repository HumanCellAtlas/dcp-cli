import sys

if sys.version_info < (3, 5):
    from scandir import scandir, walk
else:
    from os import scandir, walk

__all__ = ('scandir', 'walk')
