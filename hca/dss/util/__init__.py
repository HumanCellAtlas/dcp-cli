import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.util.compat import USING_PYTHON2

if USING_PYTHON2:
    import scandir
else:
    from os import scandir


def separator_to_camel_case(separated, separator):
    components = separated.split(separator)
    return "".join(x.title() for x in components)


def directory_builder(src_dir):
    """
        Function that recursively locates files within folder
        Note: os.scandir does not guarantee ordering
    :param src_dir:  string for directory to be parsed through
    :return an iterable of DirEntry objects all files within the src_dir
    """
    for x in os.scandir(os.path.join(src_dir)):
        if x.is_dir(follow_symlinks=False):
            for y in x:
                yield y
        else:
            yield x


def object_name_builder(file_name, src_dir):
    """
    Function creates a name to be uploaded into the manifest
    :param src_dir: string for src directory, used for removing path information
    :param file_name: filename string to be cleaned
    :return: returns a name to be used for the cloud object
    """
    """
    Creates object naming for upload based on path, attempts to normalize the paths from different OS
    :param file_name: string for path to file
    :return: a string for the object name to be used in cloud storage
    """
    file_path = os.path.normpath(os.path.join(file_name))
    root, file = os.path.split(file_path)
    if not root:
        # base case that path is just a file
        return str(file)
    else:
        intermediate_dirs = root.replace(src_dir, '')
        if intermediate_dirs.startswith("/"):
            intermediate_dirs = intermediate_dirs.lstrip("/")
        intermediate_dirs = os.path.join(intermediate_dirs, file)
        return str(intermediate_dirs)
