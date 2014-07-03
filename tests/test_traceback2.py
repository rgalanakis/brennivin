from __future__ import print_function

from StringIO import StringIO
import unittest

from brennivin import testhelpers, traceback2 as tb2


class Traceback2Tests(unittest.TestCase):
    def test_print(self):
        """
        A high-level test to get some basic coverage.
        Not super useful but better than nothing!
        More specific tests can be added when changes need to be made.
        """
        out = StringIO()
        try:
            raise SystemError()
        except SystemError:
            tb2.print_exc(file=out, show_locals=True)
        output = out.getvalue()
        lines = output.splitlines()
        try:
            self.assertEqual(lines[0], 'Traceback (most recent call last):')
            testhelpers.assertStartsWith(lines[1], '  File "')
            testhelpers.assertEndsWith(lines[1],
                                       ', in %s' % self.test_print.__name__)
            self.assertEqual(lines[2], '    raise SystemError()')
            self.assertEqual(lines[3], '                self = <tests.test_traceback2.Traceback2Tests testMethod=test_print>')
            testhelpers.assertStartsWith(lines[4], '                 out = <StringIO.StringIO instance at 0x')
            self.assertEqual(lines[-1], 'SystemError')
        except AssertionError:  # pragma: no cover
            print(output)
            raise

    def clean(self, path):
        return path.replace('.pyc', '.py').replace('.pyo', '.py')

    def test_extract_stack(self):
        stack = tb2.extract_stack()
        path, lineno, func, line, notsure = stack[-1]
        self.assertEqual(self.clean(path), self.clean(__file__))
        self.assertEqual(
            lineno,
            self.test_extract_stack.im_func.func_code.co_firstlineno + 1)
        self.assertEqual(func, self.test_extract_stack.__name__)
        self.assertEqual(line, 'stack = tb2.extract_stack()')
        self.assertIsNone(notsure)
