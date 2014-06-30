import atexit
import mock
import os
try:
    import StringIO
except ImportError:
    import io as StringIO
import unittest
import yaml

from .compat import DependenciesMissing
from brennivin import osutils, testhelpers, yamlext


def ensure_libyaml():
    if not yamlext.CIO.is_supported():
        raise DependenciesMissing('libyaml (C bindings) not found.')


def get_yaml_filepath_str_and_stream(DICT, dumper=yaml.Dumper):
    yamlfp = osutils.mktemp('.yaml')
    with open(yamlfp, 'w') as f:
        yaml.dump(DICT, f, Dumper=dumper)
    atexit.register(os.remove, yamlfp)
    yamlstr = yaml.dump(DICT, None, dumper)
    yamlstream = StringIO.StringIO(yamlstr)
    yamlstream.getvalue()  # Force it to update internally
    return yamlfp, yamlstr, yamlstream


class IOTestsMixin(object):

    assertEqual = None
    cls = None

    DICT = {'a': 'foo',
            'b': [1, 2, 3],
            'c': (4, 5, 6),
            'd': {}}
    FILE, STR, STREAM = get_yaml_filepath_str_and_stream(DICT)

    def testDumpStr(self):
        s = self.cls().dumps(self.DICT)
        self.assertEqual(s, self.STR)

    def testDumpFile(self):
        path = osutils.mktemp('.yaml')
        self.cls().dumpfile(self.DICT, path)
        testhelpers.assertTextFilesEqual(self, path, self.FILE)

    def testDumpStream(self):
        stream = StringIO.StringIO()
        self.cls().dump(self.DICT, stream)
        self.assertEqual(stream.getvalue(), self.STREAM.getvalue())

    def testLoadStr(self):
        d = self.cls().loads(self.STR)
        self.assertEqual(d, self.DICT)

    def testLoadFile(self):
        d = self.cls().loadfile(self.FILE)
        self.assertEqual(d, self.DICT)

    def testLoadStream(self):
        d = self.cls().load(self.STREAM.getvalue())
        self.assertEqual(d, self.DICT)


class TestPyIO(unittest.TestCase, IOTestsMixin):
    cls = yamlext.PyIO


class TestCIO(unittest.TestCase, IOTestsMixin):
    cls = yamlext.CIO

    def setUp(self):
        ensure_libyaml()


class TestPreferredIO(unittest.TestCase, IOTestsMixin):
    def setUp(self):
        self.cls = lambda: yamlext
        self.newvalue = testhelpers.patch(self, yamlext, '_preferred')
        self.newvalue.return_value = yamlext.PyIO()


class TestPreferredChooser(unittest.TestCase):

    def setUp(self):
        ensure_libyaml()

    def _patchAndTest(self, supported, iotype):
        with mock.patch('brennivin.yamlext.CIO.is_supported', mock.MagicMock(return_value=supported)):
            self.assertIsInstance(yamlext._preferred(), iotype)

    def testWithCIOSupported(self):
        self._patchAndTest(True, yamlext.CIO)

    def testWithCIOUnsupported(self):
        self._patchAndTest(False, yamlext.PyIO)
