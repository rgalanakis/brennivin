import os
import tempfile
import time
import unittest

from brennivin import compat, itertoolsext, osutils, testhelpers as th


class FakeTestCaseTests(unittest.TestCase):
    def testCanBeUsedAsTestCase(self):
        tc = th.FakeTestCase()
        with self.assertRaises(AssertionError):
            th.assertNumbersEqual(tc, 1, 2)
        self.assertIsInstance(tc, unittest.TestCase)


class TestAssertNumbersEqual(unittest.TestCase):
    def testDifferenceRaises(self):
        """Test that a difference more than tolerance asserts."""
        self.assertRaises(AssertionError, th.assertNumbersEqual, self, 0, 2, 1)

    def testDifferenceEqualToToleranceIsEqual(self):
        """Test that a difference equal to the tolerance does not assert."""
        th.assertNumbersEqual(self, 0, 1, 1)


class TestAssertBetween(unittest.TestCase):

    def testTrue(self):
        th.assertBetween(self, 1, 2, 3)
        th.assertBetween(self, 1, 1, 3, True)
        th.assertBetween(self, 1, 3, 3, True)

    def testFalse(self):
        def assertNotBtw(*args, **kwargs):
            self.assertRaises(AssertionError,
                              th.assertBetween, self, *args, **kwargs)
        assertNotBtw(1, 1, 3)
        assertNotBtw(1, 3, 3)
        assertNotBtw(1, 4, 3)


class TestAssertFloatsSeqEqual(unittest.TestCase):
    def testBasic(self):
        """Test that two identical sequences do not assert."""
        a = (0, 0, 0)
        b = (0, 0, 0)
        th.assertNumberSequencesEqual(self, a, b)

    def testDifferenceLessThanTolerance(self):
        """Test that an element off by less than tolerance does not assert."""
        a = (0.0, 0.0, 0.0)
        b = (1e-10, 0.0, 0.0)
        th.assertNumberSequencesEqual(self, a, b, 0.0000000001)

    def testAssertDifferenceMoreThanTolerance(self):
        """Test that an element off by more than tolerance asserts."""
        a = (0, 0, 0)
        b = (2, 0, 0)
        self.assertRaises(AssertionError,
                          th.assertNumberSequencesEqual, self, a, b, 1)

    def testDifferenceLengths(self):
        """Test that sequences of different lengths asserts."""
        a = (0, 0)
        b = (0, 0, 0)

        def assertRaise(x, y):
            self.assertRaises(AssertionError,
                              th.assertNumberSequencesEqual, self, x, y)
        assertRaise(a, b)
        assertRaise(b, a)


class AssertStartsAndEndsWithTests(unittest.TestCase):

    def testStarts(self):
        s = 'abcd'
        th.assertStartsWith(s, 'ab')
        with self.assertRaises(AssertionError):
            th.assertStartsWith(s, 'b')

    def testEnds(self):
        s = 'abcd'
        th.assertEndsWith(s, 'cd')
        with self.assertRaises(AssertionError):
            th.assertEndsWith(s, 'c')


class TestAssertPermissionbitsEqual(unittest.TestCase):

    def setUp(self):
        self._files = []

    def CreateFile(self, readonlystate):
        p = osutils.mktemp('readonlystate_%s' % readonlystate)
        osutils.set_readonly(p, readonlystate)
        self._files.append(p)
        return p

    def testIdentical(self):
        a = self.CreateFile(True)
        b = self.CreateFile(True)
        th.assertPermissionbitsEqual(self, a, b)

    def testDifferentAsserts(self):
        a = self.CreateFile(False)
        b = self.CreateFile(True)
        self.assertRaises(AssertionError,
                          th.assertPermissionbitsEqual, self, a, b)

    def tearDown(self):
        map(lambda p: osutils.set_readonly(p, False), self._files)
        map(os.remove, self._files)


class AssertTextFilesEqualTests(unittest.TestCase):

    def _getTempfile(self):
        fp = osutils.mktemp()
        self.addCleanup(os.remove, fp)
        return fp

    def write(self, data):
        """Write ``data`` to a temp file and return that file's path."""
        fp = self._getTempfile()
        with open(fp, 'wb') as f:
            f.write(data)
        return fp

    def assertEq(self, d1, d2):
        f1 = self.write(d1)
        f2 = self.write(d2)
        th.assertTextFilesEqual(self, f1, f2)

    def assertNeq(self, d1, d2):
        with self.assertRaises(AssertionError):
            self.assertEq(d1, d2)

    def testIgnoresTrailingLineWhitespace(self):
        self.assertEq(b'a\r\nb  \nc',
                      b'a\nb\nc  ')

    def testDifferentLineContentsAsserts(self):
        self.assertNeq(b'a\nb1',
                       b'a\nb2')

    def testIgnoresTrailingWhitespaceLines(self):
        self.assertEq(b'a',
                      b'a\n  \r\n \t \n')


class AssertFoldersEqualTests(unittest.TestCase):
    def testThisFolderAgainstItself(self):
        d = os.path.dirname(__file__)
        th.assertFoldersEqual(self, d, d)

    def testDifferentDirs(self):
        this = os.path.dirname(__file__)
        other = os.path.dirname(th.__file__)
        with self.assertRaises(AssertionError):
            th.assertFoldersEqual(self, this, other)


class AssertJsonEqualTests(unittest.TestCase):

    def testPrintsDiff(self):
        out = compat.StringIO()
        with self.assertRaises(AssertionError):
            th.assertJsonEqual([], [1], out)
        lines = out.getvalue().splitlines()
        # diff output includes \n\n, which becomes empty entry from splitlines
        # get rid of them.
        lines = list(filter(None, lines))
        th.assertStartsWith(lines[0], '--- calculated')
        th.assertStartsWith(lines[1], '+++ ideal')


class TestTimeMock(unittest.TestCase):

    def testPatchesAndUnpatched(self):
        getall = lambda: [getattr(time, a) for a in th.patch_time.ATTRS]
        orig = getall()
        with th.patch_time():
            self.assertNotEqual(orig, getall())
        self.assertEqual(orig, getall())

    def testSystem(self):
        with th.patch_time(starttime=100):
            self.assertEqual(time.time(), 100)
            self.assertEqual(time.clock(), 0)
            time.sleep(2)
            self.assertEqual(time.time(), 102)
            self.assertEqual(time.clock(), 2)


class TestMonkeyPatcher(unittest.TestCase):

    def testPatchesAndUnpatches(self):
        o = itertoolsext.Bundle(a=1)
        mp = th.Patcher(o, 'a', 2)
        self.assertEqual(o.a, 1)
        mp.__enter__()
        self.assertEqual(o.a, 2)
        mp.__exit__()
        self.assertEqual(o.a, 1)

    def testCanOnlyBeEnteredOnce(self):
        o = itertoolsext.Bundle(a=1)
        mp = th.Patcher(o, 'a', 1)
        mp.__enter__()
        self.assertRaises(RuntimeError, mp.__enter__)


class TestXmlCompare(unittest.TestCase):

    def assertXmlNEq(self, a, b):
        with self.assertRaises(AssertionError):
            th.assertXmlEqual(a, b)

    def testEqual(self):
        th.assertXmlEqual(
            '<root />',
            '<root>\n</root>')

    def testNodesNotEqual(self):
        self.assertXmlNEq(
            '<root><a></a></root>',
            '<root><b></b></root>')
        self.assertXmlNEq(
            '<root></root>',
            '<root><b></b></root>')

    def testTextNotEqual(self):
        self.assertXmlNEq(
            '<r><a>hi</a></r>',
            '<r><a>bye</a></r>')

    def testAttribsNotEqual(self):
        self.assertXmlNEq(
            '<r a="1"></r>',
            '<r a="2"></r>')
        self.assertXmlNEq(
            '<r a="1"></r>',
            '<r b="1"></r>')
        self.assertXmlNEq(
            '<r></r>',
            '<r b="1"></r>')

    def testStarTextMatches(self):
        a = '<r>*</r>'
        th.assertXmlEqual(a, '<r></r>')
        th.assertXmlEqual(a, '<r>hi</r>')


class CallCounterTests(unittest.TestCase):

    def test_no_params(self):
        c = th.CallCounter.no_params()
        c()
        c()
        self.assertEqual(c.count, 2)
        with self.assertRaises(TypeError):
            c(1)

    def test_all_params(self):
        c = th.CallCounter.all_params()
        self.assertEqual(1, c(1))
        c()
        c(hi=1)
        self.assertEqual(c.count, 3)
