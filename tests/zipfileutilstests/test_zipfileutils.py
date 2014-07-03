import os
import shutil
import sys
import tempfile
import unittest
import zipfile

from brennivin import osutils, testhelpers, zipfileutils as zu


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
        include = lambda p: p.endswith('.fake')
        exclude = lambda p: p.endswith('b.fake')
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


class TestCompareZipFiles(unittest.TestCase):

    def setUp(self):
        self.tempd = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tempd)

    def createZip(self, files=(('dir1/file1.txt', 'abc'),)):
        path = osutils.mktemp('.zip', dir=self.tempd)
        with zu.ZipFile(path, 'w') as z:
            for fpath, fstr in files:
                z.writestr(fpath, fstr)
        return path

    def assertAssertsWithMsg(self, z1, z2, msg, starts=False):
        try:
            zu.compare_zip_files(z1, z2)
            self.fail('Should  have raised')
        except zu.FileComparisonError as ex:
            if starts:
                firstline = ex.args[0].splitlines()[1].strip()
                self.assertTrue(
                    firstline.startswith(msg),
                    '%r should have started with %r' % (firstline, msg))
            else:
                self.assertEqual(ex.args[0], msg)

    def testEqualZips(self):
        f1 = self.createZip()
        f2 = self.createZip()
        zu.compare_zip_files(f1, f2)

    def testDifferentFileContentsRaise(self):
        f1 = self.createZip([['f1.txt', '1']])
        f2 = self.createZip([['f1.txt', '2']])
        self.assertAssertsWithMsg(f1, f2, 'f1.txt: CRC (2212294583, 450215437)', True)

    def testDifferentNumFilesRaise(self):
        f1 = self.createZip([['f1.txt', '1'], ['f2.txt', '1']])
        f2 = self.createZip([['f1.txt', '1']])
        self.assertAssertsWithMsg(
            f1, f2, "File lists differ: ['f1.txt', 'f2.txt'], ['f1.txt']")

    def testDifferentFileCasesRaise(self):
        f1 = self.createZip([['f.txt', '1']])
        f2 = self.createZip([['F.TXT', '1']])
        self.assertAssertsWithMsg(
            f1, f2, "File lists differ: ['f.txt'], ['F.TXT']")

    def testEmptyFilesBehavior(self):
        # Behavior changed in 2.7 series, not sure exactly what version
        # (2.7.0 is in shared_tools, 2.7.3 in CCP interpreter
        docompare = lambda: zu.compare_zip_files(self.createZip([]), self.createZip([]))
        if sys.version_info < (2, 7, 2):
            with self.assertRaises(zipfile.BadZipfile):
                docompare()
        else:
            docompare()
