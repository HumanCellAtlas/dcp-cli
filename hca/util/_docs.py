import CommonMark

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
