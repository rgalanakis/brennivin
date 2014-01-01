import logging
import os
import tempfile
import unittest

from brennivin import itertoolsext, osutils, logutils


class TestMultiLineIndentFormatter(unittest.TestCase):
    def createRecord(
            self, s='Line one\nLine two sits directly beneath line one'):
        rec = logging.LogRecord(
            'loggername', 30, r'test_stdlogutils.py',
            12, s, ['args'], None, func='testFormat')
        return rec

    def testFormatNoArgs(self):
        """Test the result of a MultiLineIndentFormatter with no fmt args."""
        fmtr = logutils.MultiLineIndentFormatter()
        s = fmtr.format(self.createRecord())
        ideal = 'Line one\nLine two sits directly beneath line one'
        self.assertEqual(s, ideal)

    def testFormatWithArgs(self):
        """Test the result of MultiLineIndentFormatter with formatting args
        (actually does indentation)."""
        fmtr = logutils.MultiLineIndentFormatter('%(name)s %(message)s')
        s = fmtr.format(self.createRecord())
        ideal = 'loggername Line one\n           Line two sits directly beneath line one'
        self.assertEqual(s, ideal)


class TestGetTimestampedFilename(unittest.TestCase):

    def testAgainstKnownGood(self):
        ideal = 'C:\\blah_2010-09-08-07-06-05.log'
        got = logutils.timestamped_filename(
            'C:\\blah.log', timestruct=(2010, 9, 8, 7, 6, 5, 4, 3, 0))
        self.assertEqual(ideal, got)

    def testSepIsIncluded(self):
        """Test to make sure sep argument is used."""
        ideal = 'C:\\foo\\bar---2012-12-30-23-11-59.log'
        got = logutils.timestamped_filename(
            'C:\\foo\\bar.log',
            timestruct=(2012, 12, 30, 23, 11, 59, 0, 1, 0),
            sep='---')
        self.assertEqual(ideal, got)


class TestGetFilenamesFromLoggers(unittest.TestCase):
    def createMockLogger(self, handlerFilename=None):
        logger = itertoolsext.Bundle()
        logger.handlers = []
        logger.addHandler = lambda h: logger.handlers.append(h)
        if handlerFilename:
            logger.addHandler(logging.FileHandler(handlerFilename))
        return logger

    def testExtractsOnlyFromHandlersWithBaseFilename(self):
        """Ensures that method returns filenames from all handlers with
        baseFilename, regardless of type."""
        f = osutils.mktemp()
        lo = self.createMockLogger(f)
        lo.addHandler(itertoolsext.Bundle(baseFilename=__file__))
        fns = logutils.get_filenames_from_loggers((lo,))
        ideal = sorted([__file__, f])
        self.assertEqual(sorted(fns), ideal)

    def testExtractsFileHandlers(self):
        """Ensures that method extracts filename from log file handlers."""
        f = osutils.mktemp()
        lo = self.createMockLogger(f)
        fns = logutils.get_filenames_from_loggers((lo,))
        self.assertEqual(fns, (f,))

    def testExtractDoesNotIncludeEmptyFilenames(self):
        """Test that no empty values are included in the returned log
        filenames."""
        f = osutils.mktemp()
        lo = self.createMockLogger(f)
        lo.handlers[0].baseFilename = ''  # nuke the filename
        fns = logutils.get_filenames_from_loggers((lo,))
        self.assertEqual(fns, ())

    def testDuplicateLoggersPassedInDoesNotDuplicateFilenames(self):
        """Test that passing in duplicate loggers does not return
        duplicate files."""
        f = osutils.mktemp()
        lo = self.createMockLogger(f)
        h = itertoolsext.Bundle(baseFilename=f)
        lo.addHandler(h)
        lo.addHandler(h)
        fns = logutils.get_filenames_from_loggers((lo,))
        self.assertEqual(fns, (f,))

    def testDuplicateFilenamesDoesNotDuplicateFilenames(self):
        """Test that passing in unique handlers pointing to the same
        file does not return duplicate filenames."""
        f = osutils.mktemp()
        lo = self.createMockLogger(f)
        lo.addHandler(itertoolsext.Bundle(baseFilename=f))
        lo.addHandler(itertoolsext.Bundle(baseFilename=f))
        fns = logutils.get_filenames_from_loggers((lo,))
        self.assertEqual(fns, (f,))

    def testReturnedFilenamesAreAbsolute(self):
        """Test that filenames returned are all absolute."""
        lo = self.createMockLogger('temp_deleteme.log')
        ideal = os.path.abspath('temp_deleteme.log')
        fns = logutils.get_filenames_from_loggers((lo,))
        self.assertEqual(fns, (ideal,))
        #Clean up the file
        fh = lo.handlers[0]
        fh.close()
        os.remove(fh.baseFilename)
        self.assertFalse(os.path.exists(fh.baseFilename))

    def testAgainstActualLoggingModule(self):
        """Test the collection against the actual logging module."""
        lo = logging.getLogger('TestGetFilenamesFromLoggers')
        h1 = logging.FileHandler(osutils.mktemp('.log'))
        lo.addHandler(h1)
        h2 = logging.FileHandler(osutils.mktemp('.log'))
        logging.root.addHandler(h2)

        #Can't test equality because logging may have picked up garbage.
        fns = logutils.get_filenames_from_loggers()
        self.assertTrue(h1.baseFilename in fns)
        self.assertTrue(h2.baseFilename in fns)

        lo.removeHandler(h1)
        logging.root.removeHandler(h2)


class TestRemoveFiles(unittest.TestCase):

    def assertRootContents(self, ideal):
        abspaths = [os.path.join(self.root, f) for f in os.listdir(self.root)]
        self.assertEqual(sorted(abspaths), sorted(ideal))

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.counter = 0
        self.maxDiff = None

    def mk(self, suffix=''):
        # TODO: Change mtime. Relying on sleep isn't reliable!
        self.counter += 1
        prefix = 'f%s_' % self.counter
        return osutils.mktemp(prefix=prefix, suffix=suffix, dir=self.root)

    def testIfDirNotExistRaisesError(self):
        subdir = os.path.join(self.root, 'subdir')
        self.assertRaises(OSError, logutils.remove_old_files, subdir)

    def testIfMaxFilesIsNegativeRaisesValueError(self):
        self.assertRaises(
            ValueError, logutils.remove_old_files, self.root, maxFiles=-1)

    def testIfLessThanMaxFilesNoFilesAreDelete(self):
        f1, f2 = self.mk(), self.mk()
        logutils.remove_old_files(self.root, maxFiles=4)
        self.assertRootContents([f1, f2])

    def testExcessFilesAreDeleted(self):
        f1, f2, f3, f4 = [self.mk() for _ in range(4)]
        logutils.remove_old_files(self.root, maxFiles=2)
        self.assertRootContents([f3, f4])

    def testOnlyDeletesNamePattern(self):
        f1, f2, f3 = self.mk(), self.mk('foo'), self.mk('_FOO_')
        logutils.remove_old_files(self.root, '*foo*')
        self.assertRootContents([f1, f3])

    def testErrorOnRemoveIsSwallowedAndCorrectFilesAreLeft(self):
        """Tests that if have 4 files, and remove 2 files, but one of
        those files cannot be removed, we are left with 3 files total."""
        f1, f2, f3, f4 = self.mk(), self.mk(), self.mk(), self.mk()
        with open(f1, 'rb'):
            logutils.remove_old_files(self.root, '*', maxFiles=2)
        self.assertRootContents([f1, f3, f4])

    def test0MaxFilesRemovesAll(self):
        self.mk(), self.mk()
        logutils.remove_old_files(self.root, maxFiles=0)
        self.assertRootContents([])


class TestGetTimestampedLogfileName(unittest.TestCase):
    def setUp(self):
        self.getpidmock = lambda: 1000
        self.timestruct = (2010, 9, 8, 7, 6, 5, 4, 3, 0)

    def testGetLoggingFilename(self):
        """Test that the correct logging filename can be gotten."""
        ideal = u'foo_2010-09-08-07-06-05_pid1000.log'
        result = logutils.get_timestamped_logfilename(
            'bar/foo', timestruct=self.timestruct, _getpid=self.getpidmock)
        self.assertEqual(ideal, os.path.basename(result))


class TestWrapLine(unittest.TestCase):

    def assertLine(self, ideal, *args):
        s = '|'.join(logutils.wrap_line(*args))
        self.assertEqual(s, ideal)

    def testWrapLine(self):
        self.assertLine('12345|- 678', '123456789', 2, 5)
        self.assertLine('1234|- 5', '12345', 2, 4)
        self.assertLine('1234', '12345', 1, 4)
        self.assertLine('12', '12', 1)
