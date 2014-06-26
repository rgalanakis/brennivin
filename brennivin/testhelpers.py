"""
Auxilliary classes to facilitate testing.

Members
=======
"""
from __future__ import print_function

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
