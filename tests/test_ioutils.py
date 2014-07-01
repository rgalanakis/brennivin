import mock
import socket
import time
import unittest

from brennivin import ioutils, testhelpers


class TestRetry(unittest.TestCase):

    def setUp(self):
        self.addCleanup(testhelpers.patch_time().__enter__().__exit__)

    def testRetryCount(self):
        """Test that the function is retried the proper number of times."""
        res = []

        @ioutils.retry(4)
        def wrapped():
            res.append(0)
            raise SystemError  # Raise so we retry
        self.assertRaises(SystemError, wrapped)
        self.assertEqual([0, 0, 0, 0], res)

    def testSleepMethod(self):
        """
        Test that we can pass in a sleep method.
        This is handy if you want to use blue's sleep instead of time.sleep()
        :return:
        """
        res = []

        @ioutils.retry(4, sleepfunc=time.sleep)
        def wrapped():
            res.append(0)
            raise SystemError  # Raise so we retry
        self.assertRaises(SystemError, wrapped)
        self.assertEqual([0, 0, 0, 0], res)

    def testExcFilter(self):
        """Test that exceptions not in the excFilter are propogated and retry
        is aborted."""
        res = []

        @ioutils.retry(excfilter=(NotImplementedError,))
        def wrapped():
            res.append(1)  # We should only have 1 item in res because the
                           #  exception will propogate
            raise SystemError
        self.assertRaises(SystemError, wrapped)
        self.assertEqual([1], res)

    def testExcFilterSubclass(self):
        """Test that passing in a baseclass to excFilter and raising it with a
         subclassed exception catches properly.
        """
        res = []

        @ioutils.retry(excfilter=(ArithmeticError,), attempts=2)
        def wrapped():
            res.append(1)  # We should end up with # of items == # of retries
            raise FloatingPointError
        self.assertRaises(FloatingPointError, wrapped)
        self.assertEqual([1, 1], res)

    def testReturnsWrapped(self):
        """Test that the decorator returns the value from the wrapped
        function."""
        @ioutils.retry()
        def wrapped():
            return 5
        self.assertEqual(5, wrapped())

    def calculateMinElapsed(self, attempts, wait, backoff):
        """Calculates how much time should have elapsed for all attempts."""
        total = wait
        for i in range(2, attempts):  # We don't sleep before the first or
                                      #  after the last
            total *= backoff
        return total

    def testWait(self):
        """Test that setting the wait value waits between tries."""
        self.runDelayedTest(wait=.1)

    def testBackoff(self):
        """Test that setting the backoff exponentially increases the wait
         time."""
        self.runDelayedTest(4, .05, 3)

    def testArgsValue(self):
        """Tests that invalid arguments ValueError."""
        err = ValueError
        retry = ioutils.retry
        self.assertRaises(err, retry, attempts=0)
        self.assertRaises(err, retry, attempts=-1)
        self.assertRaises(err, retry, wait=-1)
        self.assertRaises(err, retry, backoff=0)
        self.assertRaises(err, retry, backoff=-1)

    def runDelayedTest(self, attempts=3, wait=0.0, backoff=1):
        #Append an item for each attempt
        attemptsleft = [attempts]

        @ioutils.retry(attempts=attempts, wait=wait, backoff=backoff)
        def wrapped():
            attemptsleft[0] -= 1
            #Do not raise on the last attempt.
            if attemptsleft[0] > 0:
                raise Exception
            #Time how long it takes everything to run.
        t = time.time()
        wrapped()
        t2 = time.time()
        tdiff = t2 - t
        minElapsed = self.calculateMinElapsed(attempts, wait, backoff)
        self.assertTrue(tdiff > minElapsed)


class TestTimeout(unittest.TestCase):

    def setUp(self):
        self.addCleanup(testhelpers.patch_time().__enter__().__exit__)

    def testTimeoutExcRaised(self):
        """Test that a TimeoutError is raised on a timeout."""
        @ioutils.timeout(.01)
        def wrapped():
            raise RuntimeError('Should not get here!')
        # Patch the thread start/join so our function is never called.
        with mock.patch('threading.Thread.start'):
            with mock.patch('threading.Thread.join'):
                self.assertRaises(ioutils.Timeout, wrapped)

    def testTimeoutExcNotRaised(self):
        """Test that a TimeoutError is not raised if there is not a timeout."""
        res = []

        @ioutils.timeout(.5)
        def wrapped():
            res.append(1)
        wrapped()
        self.assertEqual(res, [1])

    def testExcPropogates(self):
        """Test that exceptions thrown in the function propogate."""
        @ioutils.timeout(.1)
        def wrapped():
            #An exception will be raised here that will propogate and not be
            # caught by a try/catch around the caller.
            raise NotImplementedError(
                'Ignore this exception, it is raised on an ignored thread.')
        self.assertRaises(NotImplementedError, wrapped)

    def testReturnsWrapped(self):
        """Test that the decorator returns the value
        from the wrapped function."""
        @ioutils.timeout(.1)
        def wrapped():
            return 5
        self.assertEqual(5, wrapped())


class TestIsLocalPortOpen(unittest.TestCase):
    def testIsIt(self):
        found = None
        for port in range(*ioutils.EPHEMERAL_PORT_RANGE):
            if ioutils.is_local_port_open(port):
                found = port
                break
        if found is None:
            raise AssertionError('No open port found.')
        self.assertTrue(ioutils.is_local_port_open(found))
        sock = socket.socket()
        try:
            sock.bind(('127.0.0.1', found))
            self.assertFalse(ioutils.is_local_port_open(found))
        finally:
            sock.close()
        self.assertTrue(ioutils.is_local_port_open(found))
