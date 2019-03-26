import os
from datetime import datetime
from atomicwrites import atomic_write as aw


class FSHelper(object):
    """
    Static helper class providing convenience methods for reading and writing files.
    """

    @staticmethod
    def atomic_write(filename, content):
        with aw(filename, overwrite=True, mode='wb') as f:
            f.write(content)

    @staticmethod
    def get_days_since_last_modified(filename):
        """
        :param filename: Absolute file path
        :return: Number of days since filename's last modified time
        """
        now = datetime.now()
        last_modified = datetime.fromtimestamp(os.path.getmtime(filename))
        return (now - last_modified).days
