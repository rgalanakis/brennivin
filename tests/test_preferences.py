import json
import mock
import os
import tempfile
import unittest
import yaml

from brennivin import osutils, preferences


class TestPreferences(unittest.TestCase):
    prefstype = preferences.Preferences

    def create(self, *args, **kwargs):
        kwargs.setdefault('onloaderror', mock.Mock())
        return self.prefstype(*args, **kwargs)

    def testInitMakesDirs(self):
        """Test that creating a Pickled makes dirs for its filename."""
        prefdir = tempfile.mkdtemp()
        os.rmdir(prefdir)
        self.assertFalse(os.path.exists(prefdir))
        self.create(os.path.join(prefdir, 'prefs.prefs'))
        self.assertTrue(os.path.exists(prefdir))

    def testUsesCustomPicklers(self):
        """Test that custom loader/dumper is used when reading/writing."""
        load, save = mock.Mock(), mock.Mock()
        p = self.create(osutils.mktemp(), save, load)
        self.assertEqual(1, load.call_count)
        p.save()
        self.assertEqual(1, save.call_count)

    def _testDefaultPickler(self, module):
        loadorig, dumporig = module.load, module.dump
        module.load = mock.Mock()
        module.dump = mock.Mock()
        try:
            p = self.create(osutils.mktemp())
            p.save()
            self.assertEqual(1, module.load.call_count)
            self.assertEqual(1, module.dump.call_count)
        finally:
            module.load = loadorig
            module.dump = dumporig

    def testDefaultPickler(self):
        """Test that json is used as the default loader/dumper.
        If a subclass uses a different one, override this."""
        self._testDefaultPickler(json)

    def testWorking(self):
        """Runs of a battery of gets and sets that should all work."""
        fn = osutils.mktemp()
        p = self.create(fn)
        self.assertEqual(p.get('a', 'b', 3), 3)
        p.setdefault('a', 'b', 4)
        self.assertEqual(p.get('a', 'b', 5), 4)

    def testCorruptData(self):
        """Test that the object does not raise when the data file is corrupt.
        """
        fn = osutils.mktemp()
        with open(fn, 'wb') as f:
            f.write(b'yhgh5454][][.^^%()B')
        p = self.create(fn)
        self.assertEqual(7, p.setdefault('test', 'test', 7))
        self.assertEqual(7, p.get('test', 'test', 0))
        return p

    def testInvalidData(self):
        """Test that the object does not raise when the data file does not
        contain a dictionary."""
        fn = osutils.mktemp()
        with open(fn, 'w') as f:
            f.write('abcd')
        p = self.create(fn, yaml.dump, yaml.load)
        self.assertEqual(7, p.setdefault('test', 'test', 7))
        self.assertEqual(7, p.get('test', 'test', 0))

    def testOnErrorCalledForLoadFailure(self):
        # Invoke one of the 'invalid' tests and ensure onerror was called.
        p = self.testCorruptData()
        self.assertEqual(p.onloaderror.call_count, 1)
