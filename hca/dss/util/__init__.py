import os
from scandir import scandir


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
