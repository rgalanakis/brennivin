"""
Functionality that you wish was on :mod:`os` and :mod:`os.path`.
And some that you don't!

Members
=======
"""

import binascii as _binascii
import contextlib as _contextlib
import errno as _errno
import fnmatch as _fnmatch
import os as _os
import shutil as _shutil
import stat as _stat
import tempfile as _tempfile
import threading as _threading

altsep = _os.altsep
if altsep is None:
    altsep = _os.sep


def abspathex(path, relative_to, _ignore_this=False):
    """Returns a normalized absoluted version of the pathname ``path``,
    relative to ``relativeTo`` directory.
    ``relativeTo`` must be an actual directory.

    :param path: The relative path to make absolute.
    :param relative_to: The filename to make path absolute to.
      This path will be made absolute before using it.
    :param _ignore_this: For internal use only.

    NOTE: This actually works by changing the cwd temporarily,
    but will always set it back.
    That said, there could be some side effects so use with care.
    """
    absRelativeTo = _os.path.abspath(relative_to)
    with change_cwd(absRelativeTo):
        if _ignore_this:
            raise ArithmeticError
        return _os.path.abspath(path)


_changecwd_lock = _threading.Lock()


@_contextlib.contextmanager
def change_cwd(cwd):
    """Context manager for temporarily changing the cwd.

    :param cwd: The directory to use as the cwd.
    """
    orig = None
    _changecwd_lock.acquire()
    try:
        orig = _os.getcwd()
        _os.chdir(cwd)
        yield
    finally:
        if orig is not None:
            _os.chdir(orig)
        _changecwd_lock.release()


@_contextlib.contextmanager
def change_environ(key, newvalue):
    """Context manager for temporarily changing an os.environ entry.
    A ``newvalue`` of None will delete the entry.
    """
    oldvalue = _os.environ.get(key, None)
    if newvalue is None:
        _os.environ.pop(key, None)
    else:
        _os.environ[key] = newvalue
    try:
        yield
    finally:
        if oldvalue is None:
            _os.environ.pop(key, None)
        else:
            _os.environ[key] = oldvalue


def change_ext(path, ext):
    """Changes the extension of path to be ext.
    If path has no extension, ext will be appended.

    :param path: The path.
    :param ext: The extension, should begin in a '.'.
    """
    root, ext_ = _os.path.splitext(path)
    ext_ = ext
    return root + ext_


def copy(src, dst):
    """Copies src to dst,
    recursively making directories for dst if they do not exist.

    src and dst should be filenames (not directories).
    """
    dirname = _os.path.dirname(dst)
    if not _os.path.isdir(dirname):
        _os.makedirs(dirname)
    _shutil.copy(src, dst)


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


def path_components(path):
    """Return list of a path's components."""
    folders = path.replace(altsep, _os.sep).split(_os.sep)
    result = [f for f in folders if f]
    if _os.name != 'nt' and path[0] == '/':
        result.insert(0, '/')
    return result


def purename(filename):
    """Returns the basename of a path without the extension."""
    if filename is None:
        raise TypeError('filename cannot be None.')
    f = _os.path.basename(filename)
    return _os.path.splitext(f)[0]


def set_readonly(path, state):
    mode = _stat.S_IREAD if state else _stat.S_IWRITE
    _os.chmod(path, mode)


def split3(path):
    """Returns a tuple of (dirname, filename without ext, ext)."""
    dirname, filename = _os.path.split(path)
    filename, ext = _os.path.splitext(filename)
    return dirname, filename, ext
