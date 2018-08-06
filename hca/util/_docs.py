import CommonMark

from docutils import utils
from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser as RSTParser

from .. import logger

_pagination_docstring = """
.. admonition:: Pagination

 This method supports pagination. Use ``{client_name}.{method_name}.iterate(**kwargs)`` to create a generator that
 yields all results, making multiple requests over the wire if necessary:

 .. code-block:: python

   for result in {client_name}.{method_name}.iterate(**kwargs):
       ...

 The keyword arguments for ``{client_name}.{method_name}.iterate()`` are identical to the arguments for
 ``{client_name}.{method_name}()`` listed here.
"""

_streaming_docstring = """
.. admonition:: Streaming

 Use ``{client_name}.{method_name}.stream(**kwargs)`` to get a ``requests.Response`` object whose body has not been
 read yet. This allows streaming large file bodies:

 .. code-block:: python

    fid = "7a8fbda7-d470-467a-904e-5c73413fab3e"
    with DSSClient().get_file.stream(uuid=fid, replica="aws") as fh:
        while True:
            chunk = fh.raw.read(1024)
            ...
            if not chunk:
                break

 The keyword arguments for ``{client_name}.{method_name}.stream()`` are identical to the arguments for
 ``{client_name}.{method_name}()`` listed here.
"""

def _md2rst(docstring):
    parser = CommonMark.Parser()
    ast = parser.parse(docstring)
    renderer = CommonMark.ReStructuredTextRenderer()
    return renderer.render(ast)


def _parse_docstring(docstring):
    """
    Using the sphinx RSTParse to parse __doc__ for argparse `parameters`, `help`, and `description`. The first
    rst paragraph encountered it treated as the argparse help text. Any param fields are treated as argparse
    arguments. Any other text is combined and added to the argparse description.

    example:
        \"""
         this will be the summary

         :param name: describe the parameter called name.

         this will be the descriptions

         * more description
         * more description

         This will also be in the description
        \"""

    :param str docstring:
    :return:
    :rtype: dict
    """
    settings = OptionParser(components=(RSTParser,)).get_default_values()
    rstparser = RSTParser()
    document = utils.new_document(' ', settings)
    rstparser.parse(docstring, document)
    if document.children[0].tagname != 'block_quote':
        logger.warning("The first line of the docstring must be blank.")
    else:
        document = document.children[0]

    def get_params(field_list_node, params):
        for field in field_list_node.children:
            name = field.children[0].rawsource.split(' ')
            if 'param' == name[0]:
                params[name[-1]] = field.children[1].astext()

    method_args = {'summary': '', 'params': dict(), 'description': ''}
    for node in document.children:
        if node.tagname is 'paragraph' and method_args['summary'] == '':
            method_args['summary'] = node.astext()
        elif node.tagname is 'field_list':
            get_params(node, method_args['params'])
        else:
            method_args['description'] += '\n' + node.astext()
    return method_args
