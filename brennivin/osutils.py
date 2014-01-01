"""
Functionality that you wish was on :mod:`os` and :mod:`os.path`.
And some that you don't!

Members
=======
"""

import binascii
import errno
import fnmatch
import os
import tempfile


def crc_from_filename(filename):
    """Returns the 32-bit crc for the file at filename."""
    with open(filename, 'rb') as f:
        data = f.read()
    # See python docs for reason for &
    return binascii.crc32(data) & 0xffffffff


def iter_files(directory, pattern='*'):
    """Returns a generator of files under directory that match pattern."""
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


def listdirex(path, pattern='*.*'):
    """Return absolute filepaths in ``path`` that matches ``pattern``."""
    return [os.path.join(path, fn) for fn in os.listdir(path)
            if fnmatch.fnmatch(fn, pattern)]


def makedirs(path, mode=0777):
    """Like ``os.makedirs``, but will not fail if directory exists."""
    try:
        os.makedirs(path, mode)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise
    return path


def mktemp(*args, **kwargs):
    """Returns an absolute temporary filename.
    A replacement for python's deprecated mktemp.
    Will call mkstemp and close the resultant file.

    Args are the same as tempfile.mkstemp
    """
    handle, filename = tempfile.mkstemp(*args, **kwargs)
    os.close(handle)
    return filename

