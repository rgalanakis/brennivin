"""
Functionality that you wish was on :mod:`os` and :mod:`os.path`.
And some that you don't!

Members
=======
"""

import binascii as _binascii
import errno as _errno
import fnmatch as _fnmatch
import os as _os
import stat as _stat
import tempfile as _tempfile


def crc_from_filename(filename):
    """Returns the 32-bit crc for the file at filename."""
    with open(filename, 'rb') as f:
        data = f.read()
    # See python docs for reason for &
    return _binascii.crc32(data) & 0xffffffff


def iter_files(directory, pattern='*'):
    """Returns a generator of files under directory that match pattern."""
    for root, dirs, files in _os.walk(directory):
        for basename in files:
            if _fnmatch.fnmatch(basename, pattern):
                filename = _os.path.join(root, basename)
                yield filename


def listdirex(path, pattern='*.*'):
    """Return absolute filepaths in ``path`` that matches ``pattern``."""
    return [_os.path.join(path, fn) for fn in _os.listdir(path)
            if _fnmatch.fnmatch(fn, pattern)]


def makedirs(path, mode=0o777):
    """Like ``os.makedirs``, but will not fail if directory exists."""
    try:
        _os.makedirs(path, mode)
    except OSError as err:
        if err.errno != _errno.EEXIST:
            raise
    return path


def mktemp(*args, **kwargs):
    """Returns an absolute temporary filename.
    A replacement for python's deprecated mktemp.
    Will call mkstemp and close the resultant file.

    Args are the same as tempfile.mkstemp
    """
    handle, filename = _tempfile.mkstemp(*args, **kwargs)
    _os.close(handle)
    return filename


def set_readonly(path, state):
    if state:
        # Make it read-only
        _os.chmod(path, _stat.S_IREAD)
    else:
        # Make it writeable
        _os.chmod(path, _stat.S_IWRITE)
