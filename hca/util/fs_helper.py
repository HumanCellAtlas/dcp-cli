import os, tempfile, errno, warnings
from datetime import datetime


class FSHelper(object):
    """
    Static helper class providing convenience methods for reading and writing files.
    """

    @staticmethod
    def atomic_write(filename, shared_dir, content):
        """
        Atomically writes content a to file.

        Writes to a temp file and renames file (atomic operation) to desired filename.
        To ensure atomicity, the src and dest dirs must be the same.

        :param filename: File name only (e.g. example.txt)
        :param shared_dir: Shared directory of temp and dest file
        :param content: Content to write to file
        """
        temp_filename = None
        dest_filename = os.path.join(shared_dir, filename)
        try:
            with tempfile.NamedTemporaryFile('wb', dir=shared_dir, delete=False) as temp:
                temp_filename = temp.name
                temp.write(content)
            FSHelper._atomic_rename(temp_filename, dest_filename)
        finally:
            if temp_filename and os.path.isfile(temp_filename):
                try:
                    os.remove(temp_filename)
                except EnvironmentError:
                    warnings.warn("\nFailed to clean up temporary file {}".format(temp_filename))

    @staticmethod
    def _atomic_rename(src, dest, max_retries=5):
        """
        Atomically renames a file.
        Support for Unix and Windows platforms.

        :param src: Source filename
        :param dest: Destination filename
        :param max_retries: Number of rename operation retries
        """
        for _ in range(max_retries):
            try:
                os.rename(src, dest)
                return
            except OSError as e:
                FSHelper._handle_rename_error(e, src, dest)
        warnings.warn("\nFailed to rename {} to {} after {} tries".format(src, dest, max_retries))

    @staticmethod
    def _handle_rename_error(err, src, dest):
        """
        Handles Windows specific rename error: https://docs.python.org/2/library/os.html#os.rename

        :param err: OSError
        :param src: Rename source filename
        :param dest: Rename destination filename
        """
        if err.errno == errno.EEXIST:
            try:
                os.remove(dest)
            except EnvironmentError:
                warnings.warn("\nFailed to delete {}".format(dest))
        else:
            raise Exception("\nFailed to rename {} to {}".format(src, dest), err)

    @staticmethod
    def get_days_since_last_modified(filename):
        """
        :param filename: Absolute file path
        :return: Number of days since filename's last modified time
        """
        now = datetime.now()
        last_modified = datetime.fromtimestamp(os.path.getmtime(filename))
        return (now - last_modified).days
