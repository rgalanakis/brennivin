"""
Contains utilities for working with IO,
such as the :class:`retry` and :class:`timeout` decorators,
and the :func:`is_local_port_open` function.

Also defines :class:`Timeout` which is used in IO-heavy areas of brennivin.

Members
=======
"""

import threading as _threading
import time as _time
import socket as _socket


EPHEMERAL_PORT_RANGE = 49152, 65535


class Timeout(_socket.timeout, Exception):
    pass


class retry(object):
    """Decorator used for retrying an operation multiple times. After each
    retry, the wait will be multiplied by backoff.

    :param attempts: Number of attemts to retry, total.  Must be >= 1.
    :param excfilter: Types of exceptions to catch when an attempt fails.
    :param wait: Initial amount of time to sleep before retrying. Must be >= 0.
        If 0, do not sleep between retries.
    :param backoff: Multiplier for time to sleep, multiplied by number of
        attempts. Must be >= 1.
    :param sleepfunc: The function used to sleep between retries.
      Default to :func:`time.sleep`.
    """
    def __init__(self, attempts=2, excfilter=(Exception,), wait=0, backoff=1,
                 sleepfunc=None):
        if attempts < 1:
            raise ValueError('attempts must be greater than or equal to 1.')
        if wait < 0:
            raise ValueError('wait must be greater than or equal to 0.')
        if backoff < 1:
            raise ValueError('backoff must be greater than or equal to 1.')
        self.attempts = attempts
        self.excFilter = excfilter
        self.wait = wait
        self.backoff = backoff
        self.sleep = sleepfunc or _time.sleep

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
    Raises a ``Timeout`` on timeout.

    The actual work happens on a new thread.
    Patch the timeout.start_thread method with your own compatible method
    if you do not want to use a thread to run the operation,
    such as if you want to use tasklets or greenlets from
    stackless or gevent.
    """

    @classmethod
    def start_thread(cls, target):
        t = _threading.Thread(target=target)
        t.start()
        return t

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
                try:
                    result = func(*args, **kwargs)
                    innerResult.append(result)
                except Exception as exc:
                    innerExcRaised.append(exc)
            t = type(self).start_thread(inner)
            t.join(timeout=self.timeoutSecs)
            if innerResult:
                return innerResult[0]
            if innerExcRaised:
                #Exc raised on thread so just don't return anything.
                raise innerExcRaised[0]
            raise Timeout
        return wrapped


def is_local_port_open(port):
    """Returns True if ``port`` is open on the local host. Note that this
    only checks whether the port is open at an instant in time and may
    be bound after this function checks but before it even returns!"""

    sock = _socket.socket()
    isBound = False
    try:
        sock.bind(('127.0.0.1', port))
    except _socket.error:
        isBound = True
    finally:
        sock.close()
    return not isBound
