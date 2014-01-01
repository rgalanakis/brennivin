"""
Contains utilities for working with IO,
such as the :class:`retry` and :class:`timeout` decorators,
and the :func:`is_local_port_open` function.

Also defines :class:`TimeoutError` which is used in other IO-heavy areas of brennivin.

Members
=======
"""

import threading
import time
import socket


EPHEMERAL_PORT_RANGE = 49152, 65535


class TimeoutError(socket.timeout, Exception):
    pass


class retry(object):
    """Decorator used for retrying an operation multiple times. After each
    retry, the wait will be multiplied by backoff.

    :param attempts: Number of attemts to retry, total.  Must be >= 1.
    :param excFilter: Types of exceptions to catch when an attempt fails.
    :param wait: Initial amount of time to sleep before retrying. Must be >= 0.
        If 0, do not sleep between retries.
    :param backoff: Multiplier for time to sleep, multiplied by number of
        attempts. Must be >= 1.
    :param sleepFunc: The function used to sleep between retries.
      Default to :func:`time.sleep`.
    """
    def __init__(self, attempts=2, excFilter=(Exception,), wait=0, backoff=1,
                 sleepFunc=None):
        if attempts < 1:
            raise ValueError, 'attempts must be greater than or equal to 1.'
        if wait < 0:
            raise ValueError, 'wait must be greater than or equal to 0.'
        if backoff < 1:
            raise ValueError, 'backoff must be greater than or equal to 1.'
        self.attempts = attempts
        self.excFilter = excFilter
        self.wait = wait
        self.backoff = backoff
        self.sleep = sleepFunc or time.sleep

    def __call__(self, func):
        attemptsLeft = [self.attempts]  # So we can re-use inside of inner.
        currDelay = [self.wait]

        def inner(*args, **kwargs):
            while True:
                if attemptsLeft[0] == 1:
                    #If this is the last attempt, no more retrying- just
                    # return now.
                    return func(*args, **kwargs)
                attemptsLeft[0] -= 1
                try:
                    return func(*args, **kwargs)
                except self.excFilter:
                    if currDelay[0]:
                        self.sleep(currDelay[0])
                        currDelay[0] *= self.backoff
                    return inner(*args, **kwargs)
        return inner


class timeout(object):
    """Decorator used for aborting operations after they have timed out.

    Raises a TimeoutError on timeout. Note that since the exception happens on
    another thread, the exception will be raised TWICE- on the problematic
    thread (which cannot easily be try/excepted around), and on the calling
    thread (which will raise it, but without the proper stack trace).

    Note that this starts the wrapped function on a thread. If the function
    times out, the thread will not be destroyed. This is a potential memory
    and performance leak. The only way around this is to use multiprocessing,
    which should be a future optimization.
    """
    def __init__(self, timeoutSecs=5):
        """Initialize.

        timeoutSecs: Seconds to wait before timing out.
        """
        self.timeoutSecs = timeoutSecs

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            innerResult = []
            innerExcRaised = []

            def inner():
                #Since this is on another thread, if we let it raise we'd get
                # the TimeoutError and we'd also get the actual error. So if
                # we raise, don't do the TimeoutError and instead re-raise the
                # thrown error.
                try:
                    result = func(*args, **kwargs)
                    innerResult.append(result)
                except Exception as exc:
                    innerExcRaised.append(exc)
                    raise
            t = threading.Thread(target=inner)
            t.start()
            t.join(timeout=self.timeoutSecs)
            if innerResult:
                return innerResult[0]
            if innerExcRaised:
                #Exc raised on thread so just don't return anything.
                raise innerExcRaised[0]
            raise TimeoutError
        return wrapped


def is_local_port_open(port):
    """Returns True if ``port`` is open on the local host. Note that this
    only checks whether the port is open at an instant in time and may
    be bound after this function checks but before it even returns!"""

    sock = socket.socket()
    isBound = False
    try:
        sock.bind(('127.0.0.1', port))
    except socket.error as ex:
        isBound = True
    finally:
        sock.close()
    return not isBound
