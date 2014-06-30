"""
Things to make working with threading in Python easier.
Note, you should generally avoid using threads,
but sometimes you need them!
Check out :mod:`brennivin.uthread` for a tasklet based solution.

Contains useful Thread subclasses:

- :class:`ExceptionalThread`, which brings proper exceptions to threads.
- :class:`NotAThread`, which is useful for mocking threads because it runs
  synchronously when ``start()`` is called.
- :class:`TimerExt`: A cancellable/restartable :class:`threading.Timer`.

Some useful threading-related utilities:

- :class:`ChunkIter`, useful for chunking work on a background thread
  and reporting it to another thread in chunks (useful for UI).
- :func:`memoize`, a caching decorator that can be threadsafe
  (vital if you want a singleton that has some expensive
  global state to construct, for example).
  There is also :class:`expiring_memoize` for a time-based solution.
- :class:`token`, a simple threading token that can be set/queried,
  useful for inter-thread communication.
- :class:`Signal`, used for registering and signaling events in a process.
- :func:`join_timeout`, raises an error if a thread is alive after a join.

Members
=======
"""

import inspect as _inspect
import sys as _sys
import threading as _threading
import time as _time
import traceback as _traceback

from . import _compat, dochelpers as _dochelpers


class ChunkIter(object):
    """Object that can be used to iterate over a collection on a background
    thread and report progress in a callback. This is useful when iteration
    of items is slow (such as if it is an expensive map or filter) and can
    be asynchronous.

    Iteration starts as soon as the object is created.

    :param iterable_: An iterable object, such as a list or generator. If
      the iterable is to be mapped and filtered, use ``itertools.imap`` and
      ``itertools.ifilter`` to pass in generators that perform the mapping
      and filtering, so it too can be done on the background thread.
    :param callback: A callable that takes a list of items as yielded by
      ``iterable_``.
    :param chunksize: Chunks will be reported back to ``callable`` with
      lists of ``chunksize`` items (the last chunk will be leftovers).

    If you do not want to use threading,
    override or patch the ``start_thread`` class method to use
    whatever library.
    """

    @classmethod
    def start_thread(cls, target, name):
        thread = _threading.Thread(target=target, name=name)
        thread.daemon = True
        thread.start()
        return thread

    def __init__(self, iterable_, callback, chunksize=50):
        self._isFinished = False
        self._cancelReq = False
        self.chunksize = chunksize
        self.fireCount = 0

        self.iterable = iterable_

        self._fireCallback = Signal('list')
        self._fireCallback.connect(callback)

        self.threading = _threading
        self.sleep = _time.sleep
        self.thread = type(self).start_thread(
            self._run_thread, 'ChunkIterWorker')

    def _run_thread(self):
        chunk = []
        for item in self.iterable:
            chunk.append(item)
            if len(chunk) == self.chunksize:
                self._fireCallback.emit(list(chunk))
                del chunk[:]
            if self._cancelReq:
                break
        if chunk and not self._cancelReq:
            self._fireCallback.emit(chunk)
        self._isFinished = True

    def wait_for_completion(self, timeout=None):
        """:meth:`threading.Thread.join(timeout)` on the background thread."""
        self.thread.join(timeout)

    def wait_chunks(self, chunks=1, sleepInterval=1):
        """Waits for ``chunks`` amount of chunks to be reported. Useful
        directly after initialization, to wait for some seed of items to
        be iterated.

        :param chunks: Number of chunks to wait for.
        :param sleepInterval: Amount of time to sleep before checking to
          see if new chunks are reported.
        """
        if self._isFinished:  # pragma: no cover
            # Optimization, we can't really test.
            return
        fireCnt = [0]

        def onChunk(_):
            fireCnt[0] += 1
        self._fireCallback.connect(onChunk)
        while not self._isFinished and fireCnt[0] < chunks:
            self.sleep(sleepInterval)
    WaitChunks = wait_chunks

    def is_finished(self):
        """Returns True if the iteration is finished."""
        return self._isFinished
    IsFinished = is_finished

    def cancel(self):
        """Call to cancel the iteration. Not be instantaneous."""
        self._cancelReq = True
    Cancel = cancel


class Signal(object):
    """
    Maintains a collection of delegates that can be easily fired.

    Listeners can add and remove callbacks through
    the :meth:`connect` and :meth:`disconnect` methods.
    Owners can emit the event through :meth:`emit`.

    :param eventdoc: Clients can provide info about the event signature and
      what it represents.  It serves no functional purpose but is useful for
      readability.
    :param onerror: Callable that takes (etype, evalue, tb)
      and is fired when any delegate errors.
    """

    def __init__(self, eventdoc=None,
                 onerror=_dochelpers.pretty_module_func(_traceback.print_exception)):
        self._delegates = []
        self.eventdoc = eventdoc
        self.onerror = onerror

    def connect(self, callback):
        self._delegates.append(callback)

    def emit(self, *args, **kwargs):
        dels = list(self._delegates)
        for d in dels:
            try:
                d(*args, **kwargs)
            except Exception:
                self.onerror(*_sys.exc_info())
        return len(dels)

    def disconnect(self, callback):
        self._delegates.remove(callback)


class ExceptionalThread(_threading.Thread):
    """Drop-in subclass for a regular :class:`threading.Thread`.

    If an error occurs during :meth:`run`:

    - Sets ``self.exc_info = sys.exc_info()``
    - Calls ``self.excepted.Fire(self.exc_info)``
    - If ``sys.excepthook`` is not the default, invoke it with self.exc_info.
      The default just writes to stderr, so no point using it.
    - If ``self.reraise`` is True, reraise the original error when all this
      handling is complete.

    If an error occured, it will also be raised on :meth:`join`.

    :param kwargs: Same as Thread, except with a ``reraise`` key (default None).
      If reraise is True, invoke the Thread exception handling after
      ExceptionalThread's exception handling.
      If False, do not invoke Thread's exception handling.
      If None, only invoke Thread's exception handling if ``excepted``
      has no delegates and sys.excepthook is the default.

      If you are joining on the thread at any point,
      you should always set reraise to False, since join will reraise
      any exceptions on the calling thread.

      There's usually little point using True because
      Thread's exception handling because it just writes to stderr.
    """
    def __init__(self, *args, **kwargs):
        self.reraise = kwargs.pop('reraise', None)
        _threading.Thread.__init__(self, *args, **kwargs)
        self.excepted = Signal('(etype, value, tb)')
        self.exc_info = None

    def run(self):
        # Impossible to test the reraise stuff because its only side effect
        # is writing to stderr.
        try:
            _threading.Thread.run(self)
        except Exception:
            self.exc_info = _sys.exc_info()
            defaultExceptHook = _sys.excepthook == _sys.__excepthook__
            if not defaultExceptHook:
                # http://bugs.python.org/issue1230540
                _sys.excepthook(*self.exc_info)
            hadlisteners = self.excepted.emit(self.exc_info)
            reraise = self.reraise
            if reraise is None:
                if not defaultExceptHook:
                    reraise = False
                elif hadlisteners:
                    reraise = False
                else:
                    reraise = True
            if reraise is True:
                raise

    def join(self, timeout=None):
        _threading.Thread.join(self, timeout)
        if self.exc_info:
            _compat.reraise(self.exc_info[0], self.exc_info[1], self.exc_info[2])


class NotAThread(_threading.Thread):
    """A thread whose :meth:`start` method runs synchronously.
    Useful to say ``ExceptionalThread = NotAThread`` if you want to debug
    a program without threading.
    """
    exc_info = None
    _started = False

    def start(self):
        self._started = True
        self.run()

    def join(self, timeout=None):
        if not self._started:
            raise RuntimeError("cannot join thread before it is started")


# noinspection PyProtectedMember
class TimerExt(_threading._Timer):
    """Extends the interface of :class:`threading.Timer` to allow for a
    :meth:`restart` method, which will restart the timer. May be extended in
    other ways in the future.

    :param interval: Number > 0.
    :param function: ``function(*args, **kwargs)`` that is called when the
      timer elapses.
    """

    def __init__(self, interval, function, args=(), kwargs=None):
        if float(interval) <= 0:
            raise ValueError('interval must be > 0, got %s' % interval)
        if function is None:
            raise ValueError('function cannot be None.')
        _threading._Timer.__init__(self, interval, function, args, kwargs or {})
        self._lock = _threading.Lock()
        self._restartRequested = False
        self.name = 'TimerExtThread'

    def restart(self):
        """Resets the timer. Will raise if the timer has finished."""
        with self._lock:
            # If restart is already pending, then just return.
            if self._restartRequested:
                return
            if self.finished.isSet():
                raise RuntimeError(
                    'Thread has already finished, cannot be restarted.')
            self._restartRequested = True
            # We need to set it so we wake up and restart our timer
            self.finished.set()

    def run(self):
        # Do not call the base class' run function.
        while True:
            self.finished.wait(self.interval)  # Always returns None in <= 2.6
            with self._lock:
                # If not set, it means we elapsed and are done
                timedOut = not self.finished.isSet()
                if timedOut:
                    self.finished.set()
                else:
                    cancelled = not self._restartRequested
                    if cancelled:
                        return
                    self.finished.clear()
                    self._restartRequested = False

            if timedOut:
                self.function(*self.args, **self.kwargs)
                return


def join_timeout(thread, timeout=8, errtype=RuntimeError):
    """:meth:`threading.Thread.join(timeout)` and raises ``errtype``
    if :meth:`threading.Thread.is_alive()` after join."""
    thread.join(timeout)
    if thread.is_alive():
        raise errtype('%s is still alive!' % thread)


class Token(object):
    """Defines a simple object that can be used for callbacks and
    cancellations."""

    def __init__(self):
        self._isSet = False

    def set(self):
        self._isSet = True

    def is_set(self):
        return self._isSet


def memoize(func=None, useLock=False, _lockcls=_dochelpers.ignore):
    """Decorator for parameterless functions, to cache their return value.
    This is functionally the same as using a Lazy
    instance but allows the use of true functions instead of attributes.

    Consider allowing memoization of parameterful functions, but that is
    far more complex so we don't need to do it right now.

    :param func: Filled when used parameter-less, which will use a
      non-locking memoize (so there is a potential for the function to be
      called several times).
      If func is passed, ``useLock`` *must* be False.
    :param useLock: If True, acquire a lock when evaluating func,
      so it can only be evaluated once.
    """
    def hasParameterless(func_):
        argspec = _inspect.getargspec(func_)
        return any(argspec)

    if not func and not useLock:
        raise AssertionError('If not using lock, must provide func '
                             '(decorate without params)')
    cache = []
    if callable(func):
        if hasParameterless(func):
            raise ValueError('Function cannot have parameters.')
        assert not useLock, 'Cannot use lock if func is provided.'

        def inner(*args, **kwargs):
            if not cache:
                cache.append(func(*args, **kwargs))
            return cache[0]
        return inner
    lock = (_lockcls or _threading.Lock)()

    def inner(func_):
        def inner2(*args, **kwargs):
            if not cache:
                with lock:
                    if not cache:
                        cache.append(func_(*args, **kwargs))
            return cache[0]
        return inner2
    return inner


class expiring_memoize(object):
    """
    Decorator used to cache method responses evaluated only once within an
    expiry period (seconds).

    Usage::

        import random
        class MyClass(object):
            # Create method whose value is cached for ten minutes
            @ExpiringMemoize(expiry=600)
            def randint(self):
                return random.randint(0, 100)

    """
    def __init__(self, expiry=0, gettime=None):
        self.expiry = expiry
        self.gettime = gettime or _time.time

    def __call__(self, func):
        def wrapped(*args):
            # Make sure the wrapped method has an attached cache
            try:
                cache = func._cache
            except AttributeError:
                cache = func._cache = {}

            # Try pulling the result from the cache and return it if it hasn't expired
            try:
                result, timestamp = cache[args]
                if self.gettime() - timestamp < self.expiry:
                    return result
            except KeyError:
                pass

            # if we did not get a cache hit, then call the method again and cache the result
            result = func(*args)
            cache[args] = (result, self.gettime())
            return result
        return wrapped
