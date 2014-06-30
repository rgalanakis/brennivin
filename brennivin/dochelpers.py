"""
Some helpers for creating pretty documentation.
Usually only of use with ``brennivin``
but you can use for your own purposes if you want.

You can use the ``default`` or ``unsupplied`` objects to
act as a unique sentinel,
and ``ignore`` for "private" parameters
(such as those with a leading underscore).

Members
=======
"""


def pretty_func(func, reprstr):
    """Returns a callable that has the same behavior as ``func``,
    and will return ``reprstr`` when strigified."""
    class pretty(object):
        def __call__(self, *args, **kwargs):
            return func(*args, **kwargs)

        def __repr__(self):
            return reprstr
        __str__ = __repr__
    return pretty()


def pretty_module_func(func):
    """Same as :func:`pretty_func` but for module functions
    (will automatically pull the repr string from its module and name)."""
    s = '.'.join([func.__module__, func.__name__])
    return pretty_func(func, s)


def pretty_value(value, reprstr):
    """Returns as a callable that will return ``value``
    when invoked with no parameters,
    and will return ``reprstr`` when stringified."""
    class pretty(object):
        def __call__(self):
            return value

        def __repr__(self):
            return reprstr
        __str__ = __repr__
    return pretty()

identity = pretty_func(lambda x: x, 'lambda x: x')


class _Sentinel(object):
    """Type for special dochelpers values."""
    def __init__(self, s, nonzero):
        self.s = s
        self.nonzero = nonzero

    def __repr__(self):
        return self.s
    __str__ = __repr__

    def __nonzero__(self):
        return self.nonzero

    def __bool__(self):
        return self.nonzero


default = _Sentinel('DEFAULT', True)
unsupplied = _Sentinel('DEFAULT', True)
ignore = _Sentinel('<IGNORE>', False)


def named_none(s):
    """Return an instance where ``bool(obj) == False`` and will return
    ``s`` when stringified."""
    return _Sentinel(s, False)
