"""
Contains the :class:`Preferences` class for serializing preferences.
It is very simple (prefs are a dict of dicts)
and flexible (can be serialized using user-provided functions).

Members
=======
"""

import json
import logging
import os
import sys
import traceback


logger = logging.getLogger(__name__)


class Preferences(object):
    """Handles the serialization of preferences values.  Pickled makes
    the following guarantees about its data:

    - If the file or directories does not exist, they will be created.
    - If the file exists but is corrupt (either the data is corrupt, or it
      is filled with not-a-dict), preferences will be reset.

    :param filename: The filename where preferences will be saved.
      Directories will be created automatically on init if they do not exist.
    :param onloaderror: If provided, invoke this function in the case
      of an error on Load. If None, just log out that an error occured.
      Errors on Save will still be raised, of course.

    Override the :meth:`loader`, :meth:`dumper`, and :meth:`openmode`
    methods to use a serializaer other than json.
    """

    def __init__(self, filename, onloaderror=None):

        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)

        self.prefs = {}
        self.filename = filename
        self.onloaderror = onloaderror
        self.load()

    def loader(self, fp):
        """Like ``json.load(fp)``"""
        return json.load(fp)

    def dumper(self, obj, fp):
        """Like ``json.dump(obj, fp)``"""
        return json.dump(obj, fp)

    def openmode(self):
        """'t' or 'b' indicating the way to open the persisted file."""
        return 't'

    def get(self, region, variable, defaultValue):
        """Get a preference value from the pickled data.

        :param region: The parent group that owns the variable.
        :param variable: The name of the stored variable.
        :param defaultValue: Value to return if the key or region do not exist.
        """
        try:
            return self.prefs[region][variable]
        except KeyError:
            return defaultValue

    def set(self, region, variable, value):
        """Register a value to be stored in a cPickle file.

        :param region: The parent group that owns the variable.
        :param variable: The name of the variable.
        :param value: The value to be stored as region.variable.
        """
        if not region in self.prefs:
            self.prefs[region] = {}
        self.prefs[region][variable] = value
        self.save()

    def setdefault(self, region, variable, defaultValue):
        """If :meth:`get` ``(region, variable)`` is not set, performs a
        :meth:`set` ``(region, variable, defaultValue)`` and returns ``defaultValue``.
        """
        sentinel = object()
        result = self.get(region, variable, sentinel)
        if result == sentinel:
            result = defaultValue
            self.set(region, variable, result)
        return result

    def save(self):
        """Save the internal data in a pickle file."""
        with open(self.filename, 'w' + self.openmode()) as f:
            self.dumper(self.prefs, f)

    def load(self):
        """Load a pickled file into the local prefs dict.  If the data in the
        file is not a dict, reset all prefs to be a dict."""
        try:
            if os.path.isfile(self.filename):
                with open(self.filename, 'r' + self.openmode()) as f:
                    self.prefs = self.loader(f)
        except Exception:
            if self.onloaderror:
                self.onloaderror(*sys.exc_info())
            else:
                logger.error(traceback.format_exc())
        if not isinstance(self.prefs, dict):
            self.prefs = {}
