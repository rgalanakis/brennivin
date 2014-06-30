"""
2to3 compatibility.
If this grows, just use six.
"""

import sys

if sys.version_info[0] > 2:
    PY3K = True
    # noinspection PyShadowingBuiltins
    long = int
    StringTypes = (str,)
else:
    PY3K = False
    # noinspection PyShadowingBuiltins
    long = long
    from types import StringTypes
