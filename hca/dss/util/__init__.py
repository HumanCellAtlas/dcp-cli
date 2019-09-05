import os
from builtins import FileExistsError
from ...util.compat import scandir


def separator_to_camel_case(separated, separator):
    components = separated.split(separator)
    return "".join(x.title() for x in components)


def iter_paths(src_dir):
    """
    Function that recursively locates files within folder
    Note: scandir does not guarantee ordering
    :param src_dir:  string for directory to be parsed through
    :return an iterable of DirEntry objects all files within the src_dir
    """
    for x in scandir(os.path.join(src_dir)):
        if x.is_dir(follow_symlinks=False):
            for x in iter_paths(x.path):
                yield x
        else:
            yield x


def object_name_builder(file_name, src_dir):
    """
    Function creates a name to be uploaded into the manifest
    :param src_dir: string for src directory, used for removing path information
    :param file_name: string for a path to file to be cleaned
    :return: returns a name to be used for the cloud object
    """
    return os.path.normpath(file_name).replace(src_dir, "")


def hardlink(source, link_name):
    """
    Create a hardlink in a portable way

    The code for Windows support is adapted from:
    https://github.com/sunshowers/ntfs/blob/master/ntfsutils/hardlink.py
    """
    try:
        os.link(source, link_name)
    except FileExistsError:
        # It's possible that the user created a different file with the same name as the
        # one we're trying to download. Thus we need to check the if the inode is different
        # and raise an error in this case.
        source_stat = os.stat(source)
        dest_stat = os.stat(link_name)
        # Check device first because different drives can have the same inode number
        if source_stat.st_dev != dest_stat.st_dev or source_stat.st_ino != dest_stat.st_ino:
            raise
