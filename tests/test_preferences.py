import json
import mock
import os
import pickle
import tempfile
import unittest

from brennivin import osutils, preferences


class PreferencesTests(unittest.TestCase):
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
            f.write('abcd!!!~')
        p = self.create(fn)
        self.assertEqual(7, p.setdefault('test', 'test', 7))
        self.assertEqual(7, p.get('test', 'test', 0))

    def testOnErrorCalledForLoadFailure(self):
        # Invoke one of the 'invalid' tests and ensure onerror was called.
        p = self.testCorruptData()
        self.assertEqual(p.onloaderror.call_count, 1)


class PicklePrefs(preferences.Preferences):

    def openmode(self):
        return 'b'

    def dumper(self, obj, fp):
        return pickle.dump(obj, fp)

    def loader(self, fp):
        return pickle.load(fp)


class PicklePrefsTests(PreferencesTests):
    prefstype = PicklePrefs

    def testIsNotJsonAndIsCPickle(self):
        p = self.create(osutils.mktemp())
        p.set('hi', 'there', 'you')
        with open(p.filename, 'r') as f:
            self.assertRaises(ValueError, json.load, f)
        with open(p.filename, 'rb') as f:
            pickle.load(f)
