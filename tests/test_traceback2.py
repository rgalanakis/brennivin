from __future__ import print_function

import unittest

from brennivin import compat, traceback2 as tb2


def get_funccode(func):
    if compat.PY3K:
        return func.__func__.__code__
    return func.im_func.func_code


class Traceback2Tests(unittest.TestCase):
    def test_print(self):
        """
        A high-level test to get some basic coverage.
        Not super useful but better than nothing!
        More specific tests can be added when changes need to be made.
        """
        out = compat.StringIO()
        try:
            raise SystemError()
        except SystemError:
            tb2.print_exc(file=out, show_locals=True)
        output = out.getvalue()
        lines = output.splitlines()
        try:
            self.assertEqual(lines[0], 'Traceback (most recent call last):')
            self.assertRegexpMatches(lines[1], '  File ".*test_traceback2.py", line \d\d, in test_print')
            self.assertEqual(lines[2], '    raise SystemError()')
            self.assertRegexpMatches(lines[3], '                 out = <.*String\w?O object at 0x[a-zA-Z0-9]+>')
            self.assertEqual(lines[4], '                self = <tests.test_traceback2.Traceback2Tests testMethod=test_print>')
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
            get_funccode(self.test_extract_stack).co_firstlineno + 1)
        self.assertEqual(func, self.test_extract_stack.__name__)
        self.assertEqual(line, 'stack = tb2.extract_stack()')
        self.assertIsNone(notsure)
