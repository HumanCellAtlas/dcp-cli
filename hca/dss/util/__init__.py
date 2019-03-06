def separator_to_camel_case(separated, separator):
    components = separated.split(separator)
    return "".join(x.title() for x in components)
