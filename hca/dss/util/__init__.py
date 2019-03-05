import os
import sys
from scandir import scandir
pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa


def separator_to_camel_case(separated, separator):
    components = separated.split(separator)
    return "".join(x.title() for x in components)


def directory_builder(src_dir):
    """
    Function that recursively locates files within folder
    Note: scandir does not guarantee ordering
    :param src_dir:  string for directory to be parsed through
    :return an iterable of DirEntry objects all files within the src_dir
    """
    for x in scandir(os.path.join(src_dir)):
        if x.is_dir(follow_symlinks=False):
            for x in directory_builder(x.path):
                yield x
        else:
            yield x


def object_name_builder(file_name, src_dir):
    """
    Function creates a name to be uploaded into the manifest
    :param src_dir: string for src directory, used for removing path information
    :param file_name: filename string to be cleaned
    :return: returns a name to be used for the cloud object
    """
    file_path = os.path.normpath(os.path.join(file_name))
    root, file_name = os.path.split(file_path)
    if not root:
        return str(file_name)
    else:
        intermediate_dirs = root.replace(src_dir, '')
        intermediate_dirs = os.path.join(intermediate_dirs, file_name)
        return str(intermediate_dirs)
