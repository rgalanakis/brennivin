import inspect
import os
from os.path import join
import shutil
import stat
import tempfile
import unittest

from brennivin import osutils

ROOT = '/'
if os.name == 'nt':
    ROOT = 'C:\\'

THISDIR = os.path.dirname(os.path.abspath(__file__))


class TestAbsPathEx(unittest.TestCase):
    def testSuccess(self):
        """Test result against some known values."""
        result = osutils.abspathex('foo', ROOT)
        self.assertEqual(result, join(ROOT, 'foo'))

    def testNoneRaises(self):
        """Test calling with None for the path."""
        self.assertRaises(OSError, osutils.abspathex, None, 'foo')

    def testRevertsCwdIfRaises(self):
        """Ensures that the cwd is set back to what it was
        even if the code raises.
        Ensure that 'relative' is a valid path.
        """
        cwd = os.getcwd()
        self.assertRaises(ArithmeticError, osutils.abspathex, 'path.py', ROOT, True)
        self.assertEqual(cwd, os.getcwd())


class ChangeCwdTests(unittest.TestCase):
    def setUp(self):
        self.oldcwd = os.getcwd()

    def _changeAndTest(self, doRaise=False):
        with osutils.change_cwd(THISDIR):
            self.assertEqual(os.getcwd(), THISDIR)
            if doRaise:
                raise SystemError

    def testChangesItBack(self):
        """Test that the cwd is changed back."""
        self._changeAndTest()
        self.assertEqual(self.oldcwd, os.getcwd())

    def testChangesWithError(self):
        """Tests that the cwd is changed back after an error."""
        try:
            self._changeAndTest(True)
        except SystemError:
            self.assertEqual(self.oldcwd, os.getcwd())


class TestChangeEnviron(unittest.TestCase):
    def setUp(self):
        os.environ['TESTVALUE'] = 'ABC'

    def _changeAndTest(self, doRaise=False):
        with osutils.change_environ('TESTVALUE', 'XYZ'):
            self.assertEqual(os.environ['TESTVALUE'], 'XYZ')
            if doRaise:
                raise SystemError

    def testChangesItBack(self):
        """Tests that the value is changed back."""
        self._changeAndTest()
        self.assertEqual(os.environ['TESTVALUE'], 'ABC')

    def testChangesWithError(self):
        """Test that the value is changed back on an error."""
        try:
            self._changeAndTest(True)
        except SystemError:
            self.assertEqual(os.environ['TESTVALUE'], 'ABC')

    def testDeletesIfItIsNew(self):
        self.assertNotIn('blah', os.environ)
        with osutils.change_environ('blah', 'f'):
            self.assertEqual(os.environ['blah'], 'f')
        self.assertNotIn('blah', os.environ)

    def testReentrancy(self):
        # Will lock if not reentrant
        with osutils.change_environ('blah', 'f'):
            with osutils.change_environ('spam', 'e'):
                pass


class ChangeExtTests(unittest.TestCase):
    """All tests here should include tests on various extension lengths.  This isn't required but would be complete.
        3 char with 3 char
        1 char with 3 char
        3 char with 1 char
        1 char with 1 char
        5 char with 3 char
        3 char with 5 char
        5 char with 5 char
    """
    def testWorksOnRelative(self):
        """Test that relative paths return proper value.
        """
        self.assertEqual(osutils.change_ext('spam\\eggs.txt', '.ham'), 'spam\\eggs.ham')
        self.assertEqual(osutils.change_ext('spam\\eggs.t', '.ham'), 'spam\\eggs.ham')
        self.assertEqual(osutils.change_ext('spam\\eggs.txt', '.h'), 'spam\\eggs.h')
        self.assertEqual(osutils.change_ext('spam\\eggs.t', '.h'), 'spam\\eggs.h')
        self.assertEqual(osutils.change_ext('spam\\eggs.texts', '.ham'), 'spam\\eggs.ham')
        self.assertEqual(osutils.change_ext('spam\\eggs.txt', '.hammm'), 'spam\\eggs.hammm')
        self.assertEqual(osutils.change_ext('spam\\eggs.texts', '.hammm'), 'spam\\eggs.hammm')

    def testWorksOnAbsolute(self):
        """Test that absolute paths return proper value.
        """
        self.assertEqual(osutils.change_ext('C:\\spam\\eggs.txt', '.ham'), 'C:\\spam\\eggs.ham')
        self.assertEqual(osutils.change_ext('C:\\spam\\eggs.t', '.ham'), 'C:\\spam\\eggs.ham')
        self.assertEqual(osutils.change_ext('C:\\spam\\eggs.txt', '.h'), 'C:\\spam\\eggs.h')
        self.assertEqual(osutils.change_ext('C:\\spam\\eggs.t', '.h'), 'C:\\spam\\eggs.h')
        self.assertEqual(osutils.change_ext('C:\\spam\\eggs.texts', '.ham'), 'C:\\spam\\eggs.ham')
        self.assertEqual(osutils.change_ext('C:\\spam\\eggs.txt', '.hammm'), 'C:\\spam\\eggs.hammm')
        self.assertEqual(osutils.change_ext('C:\\spam\\eggs.texts', '.hammm'), 'C:\\spam\\eggs.hammm')

    def testWorksOnFileOnly(self):
        """Test that changeExt works with only a filename."""
        self.assertEqual(osutils.change_ext('eggs.txt', '.ham'), 'eggs.ham')
        self.assertEqual(osutils.change_ext('eggs.t', '.ham'), 'eggs.ham')
        self.assertEqual(osutils.change_ext('eggs.txt', '.h'), 'eggs.h')
        self.assertEqual(osutils.change_ext('eggs.t', '.h'), 'eggs.h')
        self.assertEqual(osutils.change_ext('eggs.texts', '.ham'), 'eggs.ham')
        self.assertEqual(osutils.change_ext('eggs.txt', '.hammm'), 'eggs.hammm')
        self.assertEqual(osutils.change_ext('eggs.texts', '.hammm'), 'eggs.hammm')

    def testAppendsExt(self):
        """Test that the extension is appended if there is none."""
        self.assertEqual(osutils.change_ext('eggs', '.txt'), 'eggs.txt')
        self.assertEqual(osutils.change_ext('spam\\eggs', '.ham'), 'spam\\eggs.ham')

    def testMultipleDotsWork(self):
        """Test that paths with multiple periods work."""
        self.assertEqual(osutils.change_ext('eggs.spam.foo', '.bar'), 'eggs.spam.bar')
        self.assertEqual(osutils.change_ext('spam\\spam.spam.spam', '.bar'), 'spam\\spam.spam.bar')


class TestCopy(unittest.TestCase):
    def getRandomTempPath(self, tail=None):
        result = join(tempfile.mkdtemp(), 'a', 'b', tail or 'tail')
        self.assertFalse(os.path.isdir(result) or os.path.isfile(result))
        return result

    def makeTempFile(self):
        fd, name = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write('foo')
        return name

    def testCopyMakesDirs(self):
        """Test that copy makes dirs recursively for src."""
        path = self.getRandomTempPath('spam.eggs')

        osutils.copy(self.makeTempFile(), path)
        self.assertTrue(os.path.isfile(path))

    def testCopyRaisesIOErrorIfSrcDoesNotExist(self):
        """Test that copy raises an IO error if src does not exist (same as 'copy' contract)."""
        src = self.getRandomTempPath('spam.eggs2')
        self.assertFalse(os.path.isfile(src))
        self.assertRaises(IOError, lambda: osutils.copy(src, self.getRandomTempPath('spam.eggs')))


class CrcFromFilenameTests(unittest.TestCase):

    def testKnown(self):
        # Will this fail on other OSes?
        f = osutils.mktemp()
        self.assertEqual(osutils.crc_from_filename(f), 0)
        with open(f, 'w') as fd:
            fd.write('hello')
        self.assertEqual(osutils.crc_from_filename(f), 907060870)


class IterFilesTests(unittest.TestCase):

    def testReturnsGenerator(self):
        f = osutils.iter_files('')
        self.assertTrue(inspect.isgenerator(f))

    def testGivenPatternFindsOnlyMatches(self):
        files = list(osutils.iter_files(THISDIR, '*.py'))
        self.assertTrue(files, 'Should not be empty.')
        for f in files:
            self.assertTrue(f.endswith('.py'))

    def testCanFindThisFile(self):
        oneup = join(THISDIR, '..')
        files = [os.path.abspath(f) for f in osutils.iter_files(oneup, '*.py')]
        thispy = os.path.abspath(__file__).replace('.pyc', '.py')
        self.assertTrue(thispy in files)


class ListDirExTests(unittest.TestCase):
    def testGivenPatternFindsOnlyMatches(self):
        files = list(osutils.listdirex(THISDIR, '*osutils.py'))
        for f in files:
            self.assertTrue(f.endswith('osutils.py'))

    def testDoesNotLookRecursively(self):
        """Test that listdirex on a path one dir up does not find this file."""
        oneup = join(THISDIR, '/')
        files = [os.path.abspath(f) for f in osutils.listdirex(oneup, '*.py')]
        thispy = os.path.abspath(__file__).replace('.pyc', '.py')
        self.assertFalse(thispy in files)


class MakeDirsTests(unittest.TestCase):
    thisdir = os.path.dirname(__file__)

    def testReturnsDirName(self):
        d = osutils.makedirs(self.thisdir)
        self.assertEqual(d, self.thisdir)

    def testDoesNotRaiseIfDirExists(self):
        self.assertTrue(os.path.isdir(self.thisdir))
        self.testReturnsDirName()

    def testMakesDirIfNotExist(self):
        tempd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tempd)
        newd = join(tempd, 'a', 'b')
        self.assertFalse(os.path.isdir(newd))
        osutils.makedirs(newd)
        self.assertTrue(os.path.isdir(newd))


class TestPathComponents(unittest.TestCase):
    msg = "Bad path componentization on '%s'. Expected %s, got %s"

    def assertComponentsEqual(self, path, ideal):
        result = osutils.path_components(path)
        self.assertEqual(result, ideal, self.msg % (path, ideal, result))

    def testValidPaths(self):
        self.assertComponentsEqual(join(ROOT, 'foo', 'bar.baz'),
                                   [ROOT, 'foo', 'bar.baz'])
        self.assertComponentsEqual(join('foo', 'bar.baz'),
                                   ['foo', 'bar.baz'])

    def testForwardSlashes(self):
        self.assertComponentsEqual('c:/foo/bar.baz',
                                   ['c:/', 'foo', 'bar.baz'])
        self.assertComponentsEqual('foo/bar.baz',
                                   ['foo', 'bar.baz'])

    def testRespaths(self):
        self.assertComponentsEqual('res:/foo/bar.baz',
                                   ['res:', 'foo', 'bar.baz'])

    def testVariousPaths(self):
        d = {'': [],
             'foo': ['foo'],
             'foo/': ['foo', ''],
             'foo\\': ['foo', ''],
             '/foo': ['/', 'foo'],
             '\\foo': ['\\', 'foo'],
             'foo/bar': ['foo', 'bar'],
             '/': ['/'],
             'c:': ['c:'],
             'c:/': ['c:/'],

             # Windows is weird, here is a valid *relative* path
             # to the current working directory on drive `c`...
             'c:foo': ['c:', 'foo'],

             # ...but here is an *absolute* path on drive `c`
             'c:/foo': ['c:/', 'foo'],

             'c:/users/john/foo.txt': ['c:/', 'users', 'john', 'foo.txt'],
             'c:/users/mary major/f': ['c:/', 'users', 'mary major', 'f'],
             'c:\\users\\mary major\\f': ['c:\\', 'users', 'mary major', 'f'],
             '/users/john/foo.txt': ['/', 'users', 'john', 'foo.txt'],
             'foo/bar/baz/loop': ['foo', 'bar', 'baz', 'loop'],
             'foo/bar/baz/': ['foo', 'bar', 'baz', '']}

        for path, ideal in d.items():
            result = osutils.path_components(path)
            self.assertEqual(result, ideal, self.msg % (path, ideal, result))


class PurenameTests(unittest.TestCase):
    def testFailsForNone(self):
        self.assertRaises(TypeError, osutils.purename, None)

    def testEmptyPath(self):
        self.assertEqual('', osutils.purename(''))

    def testRelative(self):
        self.assertEqual('foo', osutils.purename(join('blah', 'foo.text')))

    def testAbsolute(self):
        """Test that method works with absolute paths."""
        self.assertEqual('spam', osutils.purename(os.path.abspath(join('eggs', 'spam.h'))))

    def testFilenameOnly(self):
        """Test that method works when passed a path-less filename."""
        self.assertEqual('eggs', osutils.purename('eggs.txt'))

    def testFilenameWithoutExtension(self):
        """Test that method returns the passed in value if it is just a plan string."""
        self.assertEqual('spam', osutils.purename('spam'))

    def testRes(self):
        self.assertEqual(
            'bar', osutils.purename('res:/foo/bar.red'))

    def testReturnsExtensionIfNoFilename(self):
        """Test that method returns the 'extension' if that is the only part of the filename.  I think this is standard
        filename behavior.
        """
        self.assertEqual('.txt', osutils.purename('.txt'))

    def testReturnsFilenameIfStartsWithDot(self):
        """Test that method returns the proper filename even if the path passed starts with a dot."""
        self.assertEqual('.spam.eggs', osutils.purename('.spam.eggs.ham'))

    def testExtractsOnlyLastIfMultipleDots(self):
        """Test that the actual extension is removed if the file has multiple dots."""
        self.assertEqual('spam.eggs', osutils.purename(join('foo', 'spam.eggs.bar')))


class SetReadOnlyTests(unittest.TestCase):

    def setUp(self):
        self.writeable = osutils.mktemp()
        self.readonly = osutils.mktemp()
        os.chmod(self.readonly, stat.S_IREAD)

    def tearDown(self):
        def safeRemove(path):
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
        safeRemove(self.readonly)
        safeRemove(self.writeable)

    def testSetReadOnlyTrue(self):
        """Test that a writeable file can be made read only."""
        osutils.set_readonly(self.writeable, True)
        self.assertFalse(os.access(self.writeable, os.W_OK))

    def testSetReadOnlyFalse(self):
        """Test that a readonly file can be made writeable."""
        osutils.set_readonly(self.readonly, False)
        self.assertTrue(os.access(self.readonly, os.W_OK))


class TestSplitPath(unittest.TestCase):
    def assertSplit(self, arg, ideal):
        got = osutils.split3(arg)
        self.assertEqual(got, ideal)

    def testAbsPaths(self):
        self.assertSplit(join(ROOT, 'foo', 'spam', 'eggs.ham'),
                         (join(ROOT, 'foo', 'spam'), 'eggs', '.ham'))
        self.assertSplit(join(ROOT, 'foo.ham'),
                         (ROOT, 'foo', '.ham'))

    def testRelativePaths(self):
        self.assertSplit(join('foo', 'ham.eggs'),
                         ('foo', 'ham', '.eggs'))
        self.assertSplit(join(ROOT, 'foo', '..', 'bar', 'eggs.ham'),
                         (join(ROOT, 'foo', '..', 'bar'), 'eggs', '.ham'))
        self.assertSplit(join('foo', '..', 'ham.eggs'),
                         (join('foo', '..'), 'ham', '.eggs'))

    def testNoDir(self):
        self.assertSplit('foo.ham', ('', 'foo', '.ham'))

    def testNoExt(self):
        self.assertSplit(join('bar', 'foo'), ('bar', 'foo', ''))

    def testEmpty(self):
        self.assertSplit('', ('', '', ''))
