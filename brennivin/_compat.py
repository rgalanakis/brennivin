"""
2to3 compatibility.
If this grows, just use six.
"""

import sys

if sys.version_info[0] > 2:
    # noinspection PyShadowingBuiltins
    long = int
    StringTypes = (str,)
else:
    # noinspection PyShadowingBuiltins
    long = long
    from types import StringTypes
