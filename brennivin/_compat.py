"""
2to3 compatibility.
If this grows, just use six.
"""

import sys
import threading

if sys.version_info[0] > 2:
    PY3K = True

    # noinspection PyShadowingBuiltins
    long = int

    StringTypes = (str,)

    def reraise(e, v, tb):
        raise e(v).with_traceback(tb)

    TimerCls = threading.Timer

    xrange = range
else:
    PY3K = False

    # noinspection PyUnresolvedReferences,PyShadowingBuiltins,PyUnboundLocalVariable
    long = long

    # noinspection PyUnresolvedReferences
    from types import StringTypes

    exec("""def reraise(e, v, tb):
    raise e, v, tb""")

    # noinspection PyUnresolvedReferences,PyProtectedMember
    TimerCls = threading._Timer

    # noinspection PyUnresolvedReferences,PyShadowingBuiltins,PyUnboundLocalVariable
    xrange = xrange