"""
Auxilliary classes to facilitate testing.

Members
=======

``unittest``: Points to the ``unittest`` module in Python >= 2.7,
and ``unittest2`` in Python <= 2.6.
This aids in creating version-agnostic test cases.

"""
from __future__ import print_function
import difflib
import json
import os as _os
import sys as _sys
import time as _time
import xml.etree.ElementTree as _elementtree

import mock as _mock

from . import (
    compat as _compat,
    dochelpers as _dochelpers,
    itertoolsext as _itertoolsext,
    osutils as _osutils,
    zipfileutils as _zipfileutils)

if _sys.version_info < (2, 7):
    try:
        # noinspection PyUnresolvedReferences,PyPackageRequirements
        import unittest2 as unittest
    except ImportError:
        raise ImportError('unittest2 required for use in <= python2.6')
else:
    # noinspection PyUnresolvedReferences
    import unittest


class FakeTestCase(unittest.TestCase):
    """
    Sometimes, you want to use one of the assertion methods in this module,
    but don't have a testcase.
    You can just use an instance of this.
    """
    def __init__(self):
        unittest.TestCase.__init__(self, '_ignoreme')

    def _ignoreme(self):
        pass


def assertBetween(tc, a, b, c, eq=False):
    """
    Asserts that::

        if eq:
            a <= b <= c
        else:
            a < b < c
    """
    le = tc.assertLessEqual if eq else tc.assertLess
    le(a, b)
    le(b, c)


def assertNumbersEqual(testcase, a, b, tolerance=0, msg=None):
    """Asserts if the sizes are not within ``tolerance``."""
    if abs(a - b) <= tolerance:
        return
    testcase.assertEqual(a, b, msg=msg)


def assertNumberSequencesEqual(testcase, a, b, tolerance=0):
    """Assert that for an element in sequence ``a`` the
    corresponding element in ``b`` is equal within ``tolerance``.

    Also assert if the two sequences are not the same length.
    """
    msg = 'Sequence length mismatch, a: %s, b: %s' % (a, b)
    testcase.assertEqual(len(a), len(b), msg)
    for i, pair in enumerate(zip(a, b)):
        element_a, element_b = pair
        try:
            assertNumbersEqual(testcase, element_a, element_b, tolerance)
        except AssertionError:
            raise AssertionError("%s != %s (element %s)" % (a, b, i))


def assertStartsWith(s, start):
    if not s.startswith(start):
        raise AssertionError('%r must start with %r' % (s, start))


def assertEndsWith(s, end):
    if not s.endswith(end):
        raise AssertionError('%r must end with %r' % (s, end))


def assertEqualPretty(testcase, calculated, ideal, msg=None):
    """Prints ideal and calculated on two lines, for easier analysis of
    what's different.  Useful for sequences.

    :param testcase: An instance of unittest.TestCase
    :param ideal: The value that should have been calculated.
    :param calculated: the value that was calculated.
    """
    try:
        testcase.assertEqual(ideal, calculated, msg)
    except AssertionError:  # pragma: no cover
        print('ideal:', ideal)
        print('calc: ', calculated)
        raise


def assertCrcEqual(testcase, calcpath, idealpath, asLib=False):
    """Asserts if crcs of paths are not equal.
    If ``DIFF_FILES_ON_CRC_FAIL`` is True, launch P4MERGE to
    diff the files.

    :param asLib: If True, do not print or show diff (function is being
      used as part of another assert function and not as a standalone).
    """
    crc1 = _osutils.crc_from_filename(calcpath)
    crc2 = _osutils.crc_from_filename(idealpath)
    testcase.assertEqual(crc1, crc2,
                         'ideal: %(idealpath)s (%(crc2)s) !='
                         ' calc: %(calcpath)s (%(crc1)s)' % locals())


def assertTextFilesEqual(testcase, calcpath, idealpath, compareLines=None):
    """Asserts if the files are not equal. It first compares crcs, and if
    that fails, it compares the file contents as text (ie, mode 'r' and not
    'rb'). The reason for this is that there can be discrepancies between
    newlines.

    :param compareLines: Callable that takes (calculated line, ideal line)
      and should assert if they are not equal. Defaults to
      ``testcase.assertEqual(calc line, ideal line)``.
    """
    if compareLines is None:
        def compareLines(linecalc_, lineideal_):
            testcase.assertEqual(linecalc_.rstrip(), lineideal_.rstrip())
    try:
        assertCrcEqual(testcase, calcpath, idealpath, asLib=True)
        return
    except AssertionError:
        pass
    with open(calcpath) as fcalc:
        with open(idealpath) as fideal:
            for linecalc, lineideal in _itertoolsext.izip_longest(
                    fcalc, fideal, fillvalue=''):
                compareLines(linecalc, lineideal)


def compareXml(x1, x2, reporter=_dochelpers.identity):
    """Compares two xml elements.
    If they are equal, return True. If not, return False.
    Differences are reported by calling the ``reporter`` parameter,
    such as ::

        reporter('Tags do not match: Foo and Bar')

    :type x1: xml.etree.ElementTree.Element
    """
    if x1.tag != x2.tag:
        reporter('Tags do not match: %s and %s' % (x1.tag, x2.tag))
        return False
    for name, value in x1.attrib.items():
        if x2.attrib.get(name) != value:
            reporter('Attributes do not match: %s=%r, %s=%r'
                     % (name, value, name, x2.attrib.get(name)))
            return False
    for name in x2.attrib.keys():
        if name not in x1.attrib:
            reporter('x2 has an attribute x1 is missing: %s'
                     % name)
            return False
    if not _compareXmlText(x1.text, x2.text):
        reporter('text: %r != %r' % (x1.text, x2.text))
        return False
    if not _compareXmlText(x1.tail, x2.tail):
        reporter('tail: %r != %r' % (x1.tail, x2.tail))
        return False
    # noinspection PyDeprecation
    cl1 = x1.getchildren()
    cl2 = x2.getchildren()
    if len(cl1) != len(cl2):
        reporter('children length differs, %i != %i'
                 % (len(cl1), len(cl2)))
        return False
    i = 0
    for c1, c2 in zip(cl1, cl2):
        i += 1
        if not compareXml(c1, c2, reporter=reporter):
            reporter('children %i do not match: %s'
                     % (i, c1.tag))
            return False
    return True


def _compareXmlText(t1, t2):
    if not t1 and not t2:
        return True
    if t1 == '*' or t2 == '*':
        return True
    return (t1 or '').strip() == (t2 or '').strip()


def assertXmlEqual(a, b):
    """Asserts two xml documents are equal.

    :type a: str, unicode, xml.etree.ElementTree.Element
    :type b: str, unicode, xml.etree.ElementTree.Element
    """
    if isinstance(a, _compat.StringTypes):
        a = _elementtree.fromstring(a)
    if isinstance(b, _compat.StringTypes):
        b = _elementtree.fromstring(b)
    diffs = []
    if not compareXml(a, b, diffs.append):
        print('XMLs not equal.')
        print('Diffs:', '\n'.join(diffs))
        print('a:', a)
        print('b:', b)
        raise AssertionError('XMLs not equal.')


def assertZipEqual(calcpath, idealpath):
    try:
        _zipfileutils.compare_zip_files(calcpath, idealpath)
        return
    except _zipfileutils.FileComparisonError as ex:
        print('%s != %s' % (calcpath, idealpath))
        raise AssertionError(ex.args[0])


def assertJsonEqual(calc, ideal, out=_sys.stderr):
    """Asserts if ``calc != ideal``.
    Will print the diff between the json dump of ``calc`` and ``ideal``
    to ``out`` before asserting,
    as a debugging aid.
    """
    if calc == ideal:
        return
    gotstr = json.dumps(calc, indent=4).splitlines()
    idealstr = json.dumps(ideal, indent=4).splitlines()
    for d in difflib.unified_diff(gotstr, idealstr, 'calculated', 'ideal'):
        print(d, file=out)
    raise AssertionError('Objects differ. See stderr output.')


def assertFoldersEqual(
        testcase, calcfolder, idealfolder,
        compare=_dochelpers.pretty_func(assertCrcEqual, 'assertCrcEqual')):
    """Asserts if any differences are found between two folders.

    :param compare: Assertion method to use.
      Pass in a custom function that switches off of extensions if you want.
    """
    def getfiles(folder):
        allfiles = list(_osutils.iter_files(folder))
        cleanfiles = map(lambda f: f.replace(folder, '').lower(), allfiles)
        return sorted(cleanfiles), allfiles

    calcClean, calcAll = getfiles(calcfolder)
    idealClean, idealAll = getfiles(idealfolder)

    try:
        assertEqualPretty(testcase, calcClean, idealClean)
        for f1, f2 in zip(calcAll, idealAll):
            compare(testcase, f1, f2)
    except AssertionError:  # pragma: no cover
        print('Compared Folders:')
        print('ideal:', idealfolder)
        print('calc: ', calcfolder)
        raise


def assertPermissionbitsEqual(
        testcase, calcpath, idealpath,
        bitgetter=_dochelpers.pretty_func(lambda p: _os.stat(p)[0], 'os.stat(<path>)[0]')):
    """Asserts if permission bits are not equal."""
    stat1 = bitgetter(calcpath)
    stat2 = bitgetter(idealpath)
    testcase.assertEqual(stat1, stat2)


class Patcher(object):
    """Context manager that stores ``getattr(obj, attrname)``, sets it
    to ``newvalue`` on enter, and restores it on exit.

    :param newvalue: If _undefined, use a new Mock.
    """
    def __init__(self, obj, attrname, newvalue=_dochelpers.default):
        self.obj = obj
        self.attrname = attrname
        if newvalue is _dochelpers.default:
            newvalue = _mock.Mock()
        self.newvalue = newvalue
        self.oldvalue = _dochelpers.default
        self._entered = False

    def __enter__(self):
        if self._entered:
            raise RuntimeError(
                'Can only enter once, or havoc would occur '
                '(setting oldvalue to the currently mocked value)')
        self._entered = True
        self.oldvalue = getattr(self.obj, self.attrname)
        setattr(self.obj, self.attrname, self.newvalue)
        return self

    def __exit__(self, *_):
        if self.oldvalue != _dochelpers.default:
            setattr(self.obj, self.attrname, self.oldvalue)


def patch(testcase, *args):
    """
    Create and enter :class:`Patcher` that will be exited
    on ``testcase`` teardown.

    :param args: Passed to the ``Patcher``.
    :return: The monkey patcher's newvalue.
    """
    mp = Patcher(*args)
    testcase.addCleanup(mp.__enter__().__exit__)
    return mp.newvalue


class patch_time(object):

    ATTRS = ['clock', 'time', 'sleep']

    def __init__(self, starttime=0):
        self.starttime = starttime
        self.old = None
        self._now = 0

    def __enter__(self):
        self.old = [(a, getattr(_time, a)) for a in self.ATTRS]
        [setattr(_time, a, getattr(self, a)) for a in self.ATTRS]
        return self

    def __exit__(self, *_):
        [setattr(_time, a, attr) for (a, attr) in self.old]

    def clock(self):
        return self._now

    def time(self):
        return self._now + self.starttime

    def sleep(self, sec):
        self._now += sec


class CallCounter(object):
    """
    Counts the number of times the instance is called.
    Available via the ``count`` attribute.

    Generally you should not create this class directly,
    and use the ``no_params`` and ``all_params`` class methods.
    Use the former when calling this should take no arguments,
    and the latter when it should take any arguments.
    """
    def __init__(self, call):
        self.count = 0
        self._call = call

    def incr(self):
        self.count += 1
        return self.count

    def __call__(self, *args, **kwargs):
        return self._call(self, *args, **kwargs)

    @classmethod
    def no_params(cls):
        return CallCounter(lambda c: c.incr())

    @classmethod
    def all_params(cls):
        return CallCounter(lambda c, *args, **kwargs: c.incr())
