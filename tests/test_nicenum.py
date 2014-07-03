import unittest

from brennivin import compat, nicenum as n


class FormatTests(unittest.TestCase):

    def assertResult(self, ideal, *args):
        self.assertEqual(n.format(*args), ideal)

    def testInt(self):
        self.assertResult('2', 2, 3)
        self.assertResult('0', 0, 3)
        self.assertResult('23,456,789', 23456789, 3)
        self.assertResult('-23,456,789', -23456789, 3)

    def testFloat(self):
        self.assertResult('124,000', 123567.0, 1000)
        self.assertResult('120,000', 123567.0, 10000)
        self.assertResult('123,567.0', 123567.0, 0.1)
        self.assertResult('0.000 000 539 2', 5.3918e-07, 1e-10)

    def testLong(self):
        self.assertResult('123', compat.long(123), 1)


class FormatMemTests(unittest.TestCase):

    def assertResult(self, ideal, val):
        self.assertEqual(n.format_memory(val), ideal)

    def testB(self):
        self.assertResult('2.0B', 2)

    def testKB(self):
        self.assertResult('1.95KB', 2000)

    def testMB(self):
        self.assertResult('1.91MB', 2000000)

    def testGB(self):
        self.assertResult('1.86GB', 2000000000)

    def testTB(self):
        self.assertResult('1862.65GB', 2000000000000)
