from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, datetime, errno

USING_PYTHON2 = True if sys.version_info < (3, 0) else False

if USING_PYTHON2:
    from pathlib2 import Path
    from funcsigs import signature, Signature, Parameter
else:
    from pathlib import Path
    from inspect import signature, Signature, Parameter
