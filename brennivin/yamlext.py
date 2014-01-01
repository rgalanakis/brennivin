"""
This module provides some utility functions for yaml,
and automatically chooses the fastest yaml loader/dumper available
automatically.

Traditional yaml usage can be replaced as follows:

Dumping to a file
-----------------
::

  with open(path, 'w') as f:
      yaml.dump(obj, f)
  =>
  yamlext.dumpfile(obj, f)


Dumping to a string
-------------------
::

  s = yaml.dump(obj)
  =>
  s = yamlext.dumps(obj)

Dumping to a stream
-------------------
Almost never a need to use this directly::

  yaml.dump(obj, stream)
  =>
  yamlext.dump(obj, stream)

Loading from a file
-------------------
::

  with open(path) as f:
      obj = yaml.load(f)
  =>
  obj = yamlext.loadfile(path)

Loading from a string
---------------------
::

  obj = yaml.load(s)
  =>
  obj = yamlext.loads(s)

Loading from a stream
---------------------
Almost never a need to use this directly::

  obj = yaml.load(stream)
  =>
  obj = yamlext.load(stream)

Members
=======
"""

import yaml


__all__ = ['dumps', 'dumpfile', 'dump', 'loads', 'loadfile', 'load']


class PyIO(object):

    def __init__(self):
        self._loader = yaml.Loader
        self._dumper = yaml.Dumper

    def dumps(self, obj, **kwargs):
        return self.dump(obj, None, **kwargs)

    def dumpfile(self, obj, path, **kwargs):
        with open(path, 'w') as f:
            self.dump(obj, f, **kwargs)

    def dump(self, obj, stream, **kwargs):
        return yaml.dump(obj, stream, Dumper=self._dumper, **kwargs)

    def loads(self, s):
        return self.load(s)

    def loadfile(self, path):
        with open(path) as f:
            return self.load(f)

    def load(self, stream):
        return yaml.load(stream, Loader=self._loader)


class CIO(PyIO):

    @classmethod
    def is_supported(cls):
        return hasattr(yaml, 'CLoader')

    def __init__(self):
        PyIO.__init__(self)
        self._loader = self._dumper = None
        if self.is_supported():
            self._loader = yaml.CLoader
            self._dumper = yaml.CDumper


def _preferred():
    if CIO.is_supported():
        return CIO()
    return PyIO()


def dumps(obj, **kwargs):
    return _preferred().dumps(obj, **kwargs)


def dumpfile(obj, path, **kwargs):
    return _preferred().dumpfile(obj, path, **kwargs)


def dump(obj, stream, **kwargs):
    return _preferred().dump(obj, stream, **kwargs)


def loads(s):
    return _preferred().loads(s)


def loadfile(path):
    return _preferred().loadfile(path)


def load(stream):
    return _preferred().load(stream)
