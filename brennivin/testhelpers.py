"""
Auxilliary classes to facilitate testing.

Members
=======
"""
from __future__ import print_function
import xml.etree.ElementTree as _elementtree

from . import dochelpers as _dochelpers, osutils as _osutils


def assertEqualPretty(testcase, ideal, calculated, msg=None):
    """Prints ideal and calculated on two lines, for easier analysis of
    what's different.  Useful for sequences.

    :param testcase: An instance of unittest.TestCase
    :param ideal: The value that should have been calculated.
    :param calculated: the value that was calculated.
    """
    try:
        testcase.assertEqual(ideal, calculated, msg)
    except AssertionError:
        print('ideal:', ideal)
        print('calc : ', calculated)
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


def compareXml(x1, x2, reporter=_dochelpers.identity):
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
    if isinstance(a, basestring):
        a = _elementtree.fromstring(a)
    if isinstance(b, basestring):
        b = _elementtree.fromstring(b)
    diffs = []
    if not compareXml(a, b, diffs.append):
        print('XMLs not equal.')
        print('Diffs:', '\n'.join(diffs))
        print('a:', a)
        print('b:', b)
        raise AssertionError('XMLs not equal.')


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
        assertEqualPretty(testcase, idealClean, calcClean)
        for f1, f2 in zip(calcAll, idealAll):
            compare(testcase, f1, f2)
    except AssertionError:
        print('Compared Folders:')
        print('ideal:', idealfolder)
        print('calc: ', calcfolder)
        raise
