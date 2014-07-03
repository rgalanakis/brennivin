"""
Like the :mod:`itertools` module but contains even more stuff!
Also puts :mod:`itertools` namespace into this module
so you can safely just use :mod:`brennivin.itertoolsext`
instead of :mod:`itertools`.

Most useful are the sequence functions based off the LINQ extension methods
in C#.

Contains the :class:`Bundle` and :class:`FrozenDict` utility types.

Contains functions for walking trees depth and breadth first.
While a depth-first recursive function is easy to write and you should
feel free to write your own instead of using :func:`treeyield_depthfirst`,
a breadth-first is much more difficult and you should consider
using :func:`treeyield_breadthfirst`.

Also contains functions for getting/setting attrs and keys of
compound objects and dicts,
such as :func:`set_compound_attr` and :func:`get_compound_item`.

Members
=======
"""

import datetime as _datetime
from itertools import *
import random as _random

from . import compat as _compat
from .dochelpers import identity as _identity, default as _unsupplied

if _compat.PY3K:
    ifilter = filter
    izip = zip
    izip_longest = zip_longest


class Bundle(dict):
    """Allowed .notation access of dict keys.

    Note that any keys that would otherwise
    hide a dict attribute will be ignored.

    >>> Bundle({'spam': 'eggs'}).spam
    'eggs'
    """
    def __init__(self, seq=None, **kwargs):
        # noinspection PyTypeChecker
        dict.__init__(self, seq or (), **kwargs)

    def __getattr__(self, item):
        return self[item]

    def __str__(self):
        clsn = self.__class__.__name__
        # You MUST call dict.__repr__, not __str__.
        # The latter causes recursion.
        return '%s(%s)' % (clsn, dict.__repr__(self))
    __repr__ = __str__


class FrozenDict(dict):
    """An immutable version of a dict.

    :raises: ``TypeError`` for any unsupported (mutable) operations.
    """
    def __raise(self, *args, **kwargs):
        raise TypeError()
    clear = pop = popitem = setdefault = update = __raise
    __delitem__ = __setitem__ = __raise

    def __hash__(self):
        # Stolen from: http://stackoverflow.com/a/2704866/1574778
        if not hasattr(self, '_hash'):
            # noinspection PyAttributeOutsideInit
            self._hash = 0
            for pair in self.items():
                self._hash ^= hash(pair)
        return self._hash


# noinspection PyShadowingBuiltins
def all(seq, predicate=bool):
    """Returns True if all items in seq return True for predicate(item)."""
    for item in seq:
        if not predicate(item):
            return False
    return True


# noinspection PyShadowingBuiltins
def any(seq, predicate=bool):
    """Returns True if any item in seq returns True for predicate(item)."""
    for item in seq:
        if predicate(item):
            return True
    return False


def bucket(seq, keyprojection=_identity, valueprojection=_identity):
    """Buckets items in seq according to their keyprojection.
    Returns a dict where the keys are all unique values from keyprojections,
    and the values are lists containing the valueprojection of all items
    in that bucket.

    >>> seq = ('a', 1), ('b', 2), ('a', 3)
    >>> bucket(seq, lambda x: x[0], lambda x: x[1])
    {'a': [1, 3], 'b': [2]}
    """
    result = {}
    for item in seq:
        thisbucket = result.setdefault(keyprojection(item), [])
        thisbucket.append(valueprojection(item))
    return result


def count(seq, predicate=None):
    """Return the number of items in seq.
    If predicate is specified,
    return the number of items in seq that predicate is true for.
    """
    i = 0
    if predicate is None:
        #if len works, use that- otherwise iterate over.
        try:
            return len(seq)
        except TypeError:
            pass
        for _ in seq:
            i += 1
    else:
        for item in seq:
            if predicate(item):
                i += 1
    return i


def datespan(startdate, enddate, delta=_datetime.timedelta(days=1)):
    """Yield datetimes while walking from startdate to enddate.
    If startdate is later than endddate,
    will count backwards starting at startdate.

    Note that startdate is inclusive (will always be the first yield),
    enddate is exclusive (it or later will never be yielded).

    :param startdate: The first date to yield.
    :param enddate: The date to stop yielding at.
    :param delta: The size of the step.

    >>> dt = _datetime.datetime
    >>> len(list(datespan(dt(2010, 2, 20), dt(2010, 4, 21))))
    60
    >>> len(list(datespan(dt(2010, 2, 20), dt(2010, 4, 21),
    ...                   _datetime.timedelta(days=2))))
    30
    >>> len(list(datespan(dt(2010, 4, 21), dt(2010, 2, 20))))
    60
    """
    # Create the comparison/increment method
    # depending on if we are reversing or not.
    if startdate < enddate:
        compare = lambda current, end: current < end
        increment = lambda current: current + delta
    else:
        compare = lambda current, end: current > end
        increment = lambda current: current - delta
    currentdate = startdate
    while compare(currentdate, enddate):
        yield currentdate
        currentdate = increment(currentdate)


def first(seq, predicate=None):
    """Return the first item in seq.
    If predicate is specified,
    return the first item in seq that predicate returns True for.
    Raises StopIteration if no item is found.
    """
    if predicate is None:
        return next(islice(seq, 1))
    filtered = ifilter(predicate, seq)
    return next(filtered)


def first_or_default(seq, predicate=None, default=None):
    """Return the first item in seq.
    If predicate is specified,
    return the first item in seq that predicate returns True for.
    Returns ``default`` if sequence is empty or no item matches criteria.
    """
    try:
        return first(seq, predicate)
    except StopIteration:
        return default


def flatmap(function, sequence):
    """Return a generator that yields the equivalent of:
    ``chain(map(function, sequence))``.

    :param function: Function that takes an item in sequence and returns
      a sequence.
    :param sequence: Any iterable object.
    """
    for item in sequence:
        subseq = function(item)
        for subitem in subseq:
            yield subitem


def groupby2(seq, keyfunc):
    """Groups a sequence by a key selector. Yields 2-item tuples of
    (key, list of items that share key).

    :param seq: Sequence of items. Items should be collections or other
      complex items. Ie, it doesn't make sense to group a list of
      integers, and such a sequence will give unpredictable results.
    :param keyfunc: Callable that takes an item in seq and returns the
      key for grouping.

    This is a more intuitive version of itertools.groupby (which is used
    internally) since it will sort the data for you, and has a more
    sensible return signature.

    >>> seq = ('a', 1), ('a', 2), ('b', 3)
    >>> dict(groupby2(seq, lambda pair: pair[0]))
    {'a': [('a', 1), ('a', 2)], 'b': [('b', 3)]}
    """
    sseq = sorted(seq, key=keyfunc)
    for key, group in groupby(sseq, keyfunc):
        yield key, list(group)


def groups_of_n(seq, n):
    """Return list of groups. A group is ``seq`` split at size ``n``.

    >>> groups_of_n([1,2,3,4,5,6], 3)
    [[1, 2, 3], [4, 5, 6]]
    """
    evenlyDivisible = len(seq) % n == 0
    if not evenlyDivisible:
        msg = 'Sequence length %s not divisible by %s' % (len(seq), n)
        raise ArithmeticError(msg)

    return [seq[i:i + n] for i in range(0, len(seq), n)]


def last(seq, predicate=None):
    """Return the last item in seq.
    If predicate is specified,
    return last item in seq that predicate returns True for.

    :raise StopIteration: If seq is empty or
      no item matches predicate criteria.
    """
    lastitem = last_or_default(seq, predicate, _unsupplied)
    if lastitem is _unsupplied:
        raise StopIteration()
    return lastitem


def last_or_default(seq, predicate=None, default=None):
    """Return the last item in seq.
    If predicate is specified,
    return the last item in seq that predicate returns true for.
    Return ``default`` if seq is empty or no item matches predicate criteria.
    """
    lastitem = default
    for item in seq:
        if predicate:
            if predicate(item):
                lastitem = item
        else:
            lastitem = item
    return lastitem


def single(seq):
    """Returns the only item in seq.
    If seq is empty or has more than one item, raise StopIteration.
    """
    #Grab the first, if it is empty the iterator will raise.
    #If the iterator doesn't raise after grabbing the second,
    # raise ourselves since seq should only have one item.
    iterator = iter(seq)
    try:
        result = next(iterator)
    except StopIteration:
        # In MayaGUI, it has SUPER strange behavior
        # (not reproducible in mayabatch) where the StopIteration
        # happens but it doesn't actually raise-
        # the execution of the script or command stops but no error
        # is apparent (for example, 'f = single([])' in the script editor
        # will not apppear to raise, but f will be unbound.
        # Catching and reraising gets around this.
        raise
    try:
        next(iterator)
    except StopIteration:
        return result
    raise StopIteration('Sequence has more than one item.')


def skip(sequence, number):
    """Returns a generator that skips ``number`` of items in ``sequence``.
    Similar to ``sequence[number:]``.
    """
    cnt = 0
    for item in sequence:
        if cnt >= number:
            yield item
        else:
            cnt += 1


def take(seq, number, predicate=None):
    """Returns a list with len <= number from items in seq."""
    if not isinstance(number, (int, float, _compat.long)):
        raise TypeError('number arg must be a number type.')
    yieldedcount = 0
    for item in seq:
        if yieldedcount >= number:
            break
        if predicate is None or predicate(item):
            yield item
            yieldedcount += 1


def unique(seq, transform=_identity):
    """Returns an iterator of unique elements in seq.
    If transform is provided,
    will apply the method to items in seq as the keys for uniqueness.
    """
    seen = set()
    for item in seq:
        marker = transform(item)
        if marker in seen:
            continue
        seen.add(marker)
        yield item
    return


def treeyield_depthfirst(node, getchildren, getchild=None, yieldnode=False):
    """Yields a tree in depth first order.

    :param node: The node to start at.
    :param getchildren: A function to return the children of 'node'.
    :param getchild: If provided, getChildren should return an int
      (the index of the child in 'node').
      This function will be called with (node, index).
    :param yieldnode: If True, yield 'node' argument.
    """
    if yieldnode:
        yield node
    childEnumerator = getchildren(node)
    if getchild:
        childEnumerator = range(childEnumerator)
    for child in childEnumerator:
        if getchild:
            child = getchild(node, child)
        for grandkid in treeyield_depthfirst(
                child, getchildren, getchild=getchild, yieldnode=True):
            yield grandkid


def treeyield_breadthfirst(node, getchildren, getchild=None, yieldnode=False):
    """Yields a tree in breadth first order.

    :param node: The node to start at.
    :param getchildren: A function to return the children of 'node'.
    :param getchild: If provided, getChildren should return an int
      (the index of the child in 'node').
      This function will be called with (node, index).
    :param yieldnode: If True, yield 'node' argument.
    """
    if yieldnode:
        yield node
    childEnumerator = getchildren(node)
    if getchild:
        childEnumerator = range(childEnumerator)
    children = []
    for child in childEnumerator:
        if getchild:
            child = getchild(node, child)
        yield child
        children.append(child)
    for child in children:
        for grandkid in treeyield_breadthfirst(
                child, getchildren, getchild=getchild):
            yield grandkid


def get_compound_item(collection, *indices):
    """
    Return the value of the element in collection that
    the indicies point to.

    E.g.::

        >>> get_compound_item(['a', {'b': 'value'}], 1, 'b')
        'value'
    """
    result = collection
    for ind in indices:
        result = result[ind]
    return result


def set_compound_item(collection, value, *indices):
    """Mutates element of collection that the indicies point to, setting it to
    value.

    E.g.::

        >>> coll = ['a', {'b': None}]
        >>> set_compound_item(coll, 'value', 1, 'b')
        >>> print coll
        ['a', {'b': 'value'}]
    """
    operative = collection
    for ind in indices[:-1]:
        operative = operative[ind]
    operative[indices[-1]] = value


def del_compound_item(collection, *indices):
    """Delete element in collection that ``indices`` point to."""
    f = get_compound_item(collection, *indices[:-1])
    del f[indices[-1]]


def _getattr_from_compound_element(obj, e):
    """Get attribute ``e`` from ``obj``.

    If ``e`` is an int the attr is assumed to be a sequence
    and the corresponding entry is returned,
    otherwise ``e`` is an attr name that is accessed using ``getattr``.
    """
    if isinstance(e, int):
        attr = obj[e]
    else:
        attr = getattr(obj, e)
    return attr


def get_compound_attr(obj, *namesandindices):
    """Like ``getattr``, but takes a sequence of names and indices
    to get compound attr from ``obj``.

    ``get_compound_attr(x, ['y', 0, 'z']`` is equivalent to ``x.y[0].z``.
    """
    currentattr = obj
    for e in namesandindices:
        currentattr = _getattr_from_compound_element(currentattr, e)
    return currentattr


def set_compound_attr(obj, value, *namesandindices):
    """Like ``setattr``, but takes a sequence of names and indices
    to set compound attr on ``obj``.

    ``set_compound_attr(x, ['y', 0, 'z'], v)``
    is equivalent to
    ``x.y[0].z = v``.
    """
    currentattr = obj
    for e in namesandindices[:-1]:
        currentattr = _getattr_from_compound_element(currentattr, e)
    setattr(currentattr, namesandindices[-1], value)


def dict_add(alpha, beta, adder_function=None):
    """Adds any keys and valued from the second given dictionary to the first
    one using the given adder function. Any keys in the beta dict not present
    in alpha will be added there as they are in beta. If alpha and beta share
    keys, the adder function is applied to their values. If no adder function
    is supplied a simple numerical addition is used.

    An adder function should take in two parameters, the value from alpha and
    the value from beta in those cases where they share keys, and should
    return the desired value after addition.

    Example:

        >>> summary = {'done': 38, 'errors': 0}
        >>> current = {'done': 4, 'warnings': 3}
        >>> dict_add(summary, current)
        >>> print summary
        {'errors': 0, 'done': 42, 'warnings': 3}

    :param alpha: The dict to add stuff to
    :type alpha: dict
    :param beta: The dict supplying stuff
    :type beta: dict
    :type adder_function: function
    """
    if adder_function is None:
        adder_function = lambda value_a, value_b: value_a + value_b

    for key in beta:
        if key in alpha:
            alpha[key] = adder_function(alpha[key], beta[key])
        else:
            alpha[key] = beta[key]


def shuffle(col, maxattempts=5):
    """Return a new shuffled collection and ensure it is shuffled.
    A regular random.shuffle could return the same as
    the input for small sequences.

    Asserts after more than maxattempts at shuffle have been made.
    """
    ret = list(col)
    if not ret or len(ret) == 1:
        return ret
    attempts = 0
    while True:
        _random.shuffle(ret)
        if col != ret:
            return ret
        attempts += 1
        if attempts > maxattempts:
            raise AssertionError("Could not get a shuffle in %s attempts." % maxattempts)
