"""
2to3 compatibility.
If this grows, just use six.
"""

import sys
import threading
2
if sys.version_info[0] > 2:
    PY3K = True
    # noinspection PyShadowingBuiltins
    long = int
    StringTypes = (str,)
    def reraise(e, v, tb):
        raise e(v).with_traceback(tb)
    TimerCls = threading.Timer
else:
    PY3K = False
    # noinspection PyShadowingBuiltins
    long = long
    from types import StringTypes
    exec("""def reraise(e, v, tb):
    raise e, v, tb""")
    TimerCls = threading._Timer
