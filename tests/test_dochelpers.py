import sys
import unittest

from brennivin import dochelpers


class TestDocHelpers(unittest.TestCase):

    def assertRepr(self, val, ideal):
        self.assertEqual(repr(val), ideal)

    def testFunc(self):
        p = dochelpers.pretty_func(lambda i: 5 + i, 'hello')
        self.assertEqual(p(1), 6)
        self.assertRepr(p, 'hello')

    def testModuleFunc(self):
        p2 = dochelpers.pretty_module_func(sys.exc_info)
        self.assertEqual(len(p2()), 3)
        self.assertRepr(p2, 'sys.exc_info')

    def testValue(self):
        p = dochelpers.pretty_value(5, 'hi')
        self.assertEqual(p(), 5)
        self.assertRepr(p, 'hi')

    def testIdentity(self):
        self.assertEqual(dochelpers.identity('a'), 'a')
        self.assertRepr(dochelpers.identity, 'lambda x: x')

    def testDefault(self):
        self.assertIsInstance(dochelpers.default, object)
        self.assertRepr(dochelpers.default, 'DEFAULT')

    def testNamedNone(self):
        n = dochelpers.named_none('foo')
        self.assertFalse(n)
        self.assertRepr(n, 'foo')
