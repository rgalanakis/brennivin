import inspect
import os
import shutil
import tempfile
import unittest

from brennivin import osutils

THISDIR = os.path.dirname(os.path.abspath(__file__))


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
        oneup = os.path.join(THISDIR, '..')
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
        oneup = os.path.join(THISDIR, '/')
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
        newd = os.path.join(tempd, 'a', 'b')
        self.assertFalse(os.path.isdir(newd))
        osutils.makedirs(newd)
        self.assertTrue(os.path.isdir(newd))