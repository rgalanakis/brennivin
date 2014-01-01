import os
import shutil
import tempfile
import unittest
import zipfile

from brennivin import testhelpers, zipfileutils as zu


THISDIR = os.path.dirname(__file__)
TESTROOT = os.path.join(THISDIR, 'testroot')
IDEAL_ALL = os.path.join(THISDIR, 'testroot_all.zip')
IDEAL_FILTERED = os.path.join(THISDIR, 'testroot_filtered.zip')
IDEAL_SUBDIR = os.path.join(THISDIR, 'testroot_subdir.zip')


class ZipFileUtilsTests(unittest.TestCase):

    def setUp(self):
        self.tempd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempd)
        self.zippath = os.path.join(self.tempd, self._testMethodName + '.zip')

    def assertZip(self, ideal):
        testhelpers.assertZipEqual(self.zippath, ideal)

    def testZipDirAll(self):
        zu.zip_dir(TESTROOT, self.zippath)
        self.assertZip(IDEAL_ALL)

    def testZipDirFiltered(self):
        include = lambda p: p.endswith('.txt')
        exclude = lambda p: p.endswith('b.txt')
        zu.zip_dir(TESTROOT, self.zippath, include, exclude)
        self.assertZip(IDEAL_FILTERED)

    def testWriteDirWithSubdir(self):
        def makeinclude(prefix):
            return lambda p: os.path.split(p)[1].startswith(prefix)

        with zu.ZipFile(self.zippath, 'w', zipfile.ZIP_DEFLATED) as zfile:
            zu.write_dir(TESTROOT, zfile, makeinclude('a'), subdir='nested1')
            zu.write_dir(TESTROOT, zfile, makeinclude('b'), subdir='nested2')
        self.assertZip(IDEAL_SUBDIR)

    def testIsInsideZipfile(self):
        test_path = os.path.join(IDEAL_ALL, "testdir", "testfile.txt")
        self.assertTrue(zu.is_inside_zipfile(test_path))
