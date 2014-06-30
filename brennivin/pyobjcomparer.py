"""
Module for comparing arbitrary python object structures using the
:func:`compare` function.

Uses a map of type to comparison method to perform comparisons recursively.

This module can be pretty easily refactored so that the comparison methods,
tolerance, etc., are customizable.

This module is necessary so we can customize the built-in behavior of
python's structure comparer, which very almost suits our needs,
except for comparison of floats and similar.

Members
=======
"""
from pprint import pformat as _pformat

from . import _compat


TOLERANCE = 0.0001


def _compare_default(a, b, _):
    return a == b


def _compare_number(a, b, _):
    return abs(a - b) < TOLERANCE


def _compare_set(a, b, breadcrumb):
    if not isinstance(b, set):
        return False
    a = sorted(a)
    b = sorted(b)
    return _compare(a, b, breadcrumb)


def _compare_tuple(a, b, breadcrumb):
    if not isinstance(b, tuple):
        return False
    return _compare(list(a), list(b), breadcrumb)


def _compare_list(a, b, breadcrumb):
    if not isinstance(b, list):
        return False
    if len(a) != len(b):
        return False
    for i, (aitem, bitem) in enumerate(zip(a, b)):
        eq = _compare(aitem, bitem, breadcrumb)
        if not eq:
            breadcrumb.append(i)
            return False
    return True


def _compare_dict(a, b, breadcrumb):
    if not isinstance(b, dict):
        return False
    sorted_a_keys = sorted(a.keys())
    sorted_b_keys = sorted(b.keys())
    eq = _compare(sorted_a_keys, sorted_b_keys, breadcrumb)
    if not eq:
        return False
    for akey, bkey in zip(sorted_a_keys, sorted_b_keys):
        aval = a[akey]
        bval = b[bkey]
        eq = _compare(aval, bval, breadcrumb)
        if not eq:
            breadcrumb.append(akey)
            return False
    return True


MAP = {int: _compare_number,
       str: _compare_default,
       _compat.long: _compare_number,
       set: _compare_set,
       list: _compare_list,
       tuple: _compare_tuple,
       dict: _compare_dict,
       float: _compare_number,
       object: _compare_default
       }


def compare(a, b):
    """Returns ``True`` if ``a`` equals ``b`` using the special sauce logic,
    ``False`` if not.

    :rtype: bool
    """
    return _compare(a, b, [])


def _compare(a, b, breadcrumb):
    comparer_func = MAP.get(type(a), _compare_default)
    eq = comparer_func(a, b, breadcrumb)
    return eq


def get_compound_diff(a, b):
    """If ``a != b`` return list of compound elements
    from ``a`` that leads to the differing value.

    If ``a == b`` return empty list.

    >>> a = [{'first': [{'second': 0}]}]
    >>> b = [{'first': [{'second': 1}]}]
    >>> get_compound_diff(a, b)
    [0, 'first', 0, 'second']


    An edge-case exists where ``a != b``, but the point of inequality
    occurs immediately, without traversing into the input structures
    (e.g. if one or both inputs are not lists or dicts).
    In this case the returned list becomes ``[a, b]``.

    >>> get_compound_diff(object(), 'foo')  # doctest: +ELLIPSIS
    [<object object at 0x...>, 'foo']

    :rtype: list
    """
    crumbs = []
    eq = _compare(a, b, crumbs)
    crumbs.reverse()
    if not eq and not crumbs:
        return [a, b]
    return crumbs


def assert_compare(a, b):
    """Raise AssertionError if ``a`` != ``b``, else return None."""
    path = get_compound_diff(a, b)
    if path:
        raise AssertionError(
            "Value at compound %s does not match:\n"
            "a: %s\n"
            "b: %s" % (path, _pformat(a), _pformat(b)))
