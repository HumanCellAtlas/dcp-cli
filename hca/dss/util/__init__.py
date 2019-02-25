import os

def separator_to_camel_case(separated, separator):
    components = separated.split(separator)
    return "".join(x.title() for x in components)


def directory_builder(src_dir: str):
    """
    Function that recursively locates files within folder
    :param src_dir:  string for directory to be parsed through
    :return an iterable of DirEntry objects all files within the src_dir
    """
    for x in os.scandir(os.path.join(src_dir)):
        if x.is_dir(follow_symlinks=False):
            yield from directory_builder(x)
        else:
            yield x
