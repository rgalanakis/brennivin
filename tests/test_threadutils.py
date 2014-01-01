import mock
import sys
import threading
import time
import unittest

from brennivin import testhelpers, threadutils


class TestChunkIter(unittest.TestCase):
    def runMapper(self, items, wait=True, **kwargs):
        returned = []

        def callback(arg):
            returned.append(arg)

        # Passing a callback will start automatically
        t = threadutils.ChunkIter(items, callback, **kwargs)
        if wait:
            t.wait_for_completion()
        return t, returned

    def _waitForGo(self):
        while not hasattr(self, 'go'):
            pass
        yield 1

    def testIsThreadedAndWaitsAndIsFinished(self):
        """Tests that the default ChunkIter:

        - Does not block the main thread.
        - IsFinished behaves properly.
        - WaitForCompletion blocks to wait for completion.
        """
        chunker, res = self.runMapper(self._waitForGo(), wait=False)
        self.assertFalse(chunker.is_finished())
        self.go = True
        chunker.wait_for_completion()
        self.assertTrue(chunker.is_finished())

    def testChunkSizeIsUsed(self):
        """Test that items are reported with the given chunk size and
        return any remaining chunks."""
        chunker, returned = self.runMapper(range(7), chunksize=5)
        self.assertEqual(len(returned[0]), 5)
        self.assertEqual(len(returned[1]), 2)

    def testWaitForCompletionBlocks(self):
        """Test that WaitForCompletion blocks for a given timeout."""
        chunker, res = self.runMapper(self._waitForGo(), wait=False)
        chunker.wait_for_completion(timeout=0.01)
        self.assertFalse(chunker.is_finished())
        self.go = True
        chunker.wait_for_completion()
        self.assertTrue(chunker.is_finished())

    def testCancel(self):
        """Test that canceling will cancel the iteration."""
        def infinity():
            while True:
                yield 1
        chunker, res = self.runMapper(infinity(), wait=False)
        self.assertFalse(chunker.is_finished())
        chunker.cancel()
        chunker.wait_for_completion()
        self.assertTrue(chunker.is_finished())

    def testWaitChunks(self):
        """Tests that WaitChunks returns immediately if already finished. This
        stuff is a bit confusing, sorry, but there's no better way to test
        it unfortunately.
        """
        def waitForGo():
            def wait():
                while not hasattr(self, 'go'):
                    pass
                del self.go

            wait()
            yield 1
            yield 1
            wait()
            yield 1

        chunker, res = self.runMapper(waitForGo(), wait=False, chunksize=1)
        self.assertFalse(chunker.is_finished())
        self.go = True
        chunker.wait_chunks(2, sleepInterval=.01)
        self.assertFalse(chunker.is_finished())
        self.assertEqual(res, [[1]] * 2)
        self.go = True
        chunker.wait_chunks(sleepInterval=.01)
        self.assertTrue(chunker.is_finished())
        self.assertEqual(res, [[1]] * 3)


class TestSignalV1(unittest.TestCase):
    def callback(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs

    def testAdd(self):
        e = threadutils.Signal()
        e.connect(self.callback)
        e.emit(1, b=2)
        self.assertEqual(self.args, (1,))
        self.assertEqual(self.kwargs, {'b': 2})

    def testRemove(self):
        e = threadutils.Signal()
        e.connect(self.callback)
        e.disconnect(self.callback)
        e.emit(1, b=2)
        self.assertFalse(hasattr(self, 'args'))
        self.assertFalse(hasattr(self, 'kwargs'))


class TestSignalV2(unittest.TestCase):

    def setUp(self):
        self.onerr = mock.Mock()
        self.m = mock.Mock()
        self.sig = threadutils.Signal(onerror=self.onerr)

    def testConnectWillRegisterEvent(self):
        self.sig.connect(self.m)
        self.sig.emit(1)
        self.sig.emit(2)
        self.assertEqual(self.m.call_args_list, [((1,),), ((2,),)])

    def testDisconnectWillDeregisterEvent(self):
        self.sig.connect(self.m)
        self.sig.emit(1)
        self.sig.disconnect(self.m)
        self.sig.emit(2)
        self.assertEqual(self.m.call_args_list, [((1,),)])

    def testDisconnectWithMissingCallbackRaises(self):
        self.assertRaises(ValueError, self.sig.disconnect, self.m)

    def testCallbacksFiredInOrder(self):
        m2 = mock.Mock()

        def mside():
            self.assertFalse(m2.called)

        def m2side():
            self.assertTrue(self.m.called)

        self.m.side_effect = mside
        m2.side_effect = m2side
        self.sig.connect(self.m)
        self.sig.connect(m2)
        self.sig.emit()
        self.assertTrue(self.m.called)
        self.assertTrue(m2.called)

    def testCallbacksAfterErroringCallbacksAreStillFired(self):
        m2 = mock.Mock()
        self.m.side_effect = NotImplementedError()
        self.sig.connect(self.m)
        self.sig.connect(m2)
        self.sig.emit()
        self.assertTrue(self.m.called)
        self.assertTrue(m2.called)

    def testErroringCallbackUsesErrorCallback(self):
        self.m.side_effect = NotImplementedError()
        self.sig.connect(self.m)
        self.sig.emit()
        self.assertEqual(self.onerr.call_count, 1)
        self.assertEqual(len(self.onerr.call_args[0]), 3)


class TestExceptionalThread(unittest.TestCase):
    """Tests for the ExceptionalThread class.
    We have two sources of difficulty (async tests are hard...):

    - Joining can sometimes timeout. So we use a TimeoutJoin, to make sure
      our tests don't hang.
    - Threads started in one test can die during a later test.
      This can be a problem if they invoke threading.Thread's exception
      handling, which causes a global side effect (writes to stderr)
      which is inspected as part of a later test.

      Ie, ThreadA starts in Test1. It passes (but ThreadA is still going).
      Test2 mocks out sys.stderr and starts ThreadB, and tests that ThreadB
      does not write ot sys.stderr. However when ThreadA dies it writes to
      sys.stderr, while Test2 is going. Test2 fails because sys.stderr was
      written to!

      Using reraise=False as the default for threads in this test will
      supress the global side effect which should hopefully make the tests
      more reliable.
    """

    def newthread(self, start=False, reraise=False):
        t = threadutils.ExceptionalThread(
            name='Thread-' + self._testMethodName,
            target=self.target, reraise=reraise)
        if start:
            t.start()
        return t

    def target(self):
        raise NotImplementedError(
            'Ignore this error. From %s.%s' % (
                type(self), self._testMethodName))

    def excCB(self, *_):
        self.excFired = True

    def testExceptedFires(self):
        t = self.newthread()
        t.excepted.connect(self.excCB)
        t.start()
        try:
            threadutils.join_timeout(t)
        except NotImplementedError:
            pass
        self.assertTrue(self.excFired)
        self.assertTrue(t.exc_info)

    def testExceptsOnJoin(self):
        t = self.newthread(start=True)
        try:
            threadutils.join_timeout(t)
            self.fail('Should have raised a NotImplementedError.')
        except NotImplementedError:
            pass

    def testCallsExcepthook(self):
        eh = mock.Mock()
        with testhelpers.Patcher(sys, 'excepthook', eh):
            t = self.newthread(start=True)
            self.assertRaises(NotImplementedError, threadutils.join_timeout, t)
        # noinspection PyArgumentList
        eh.assert_called_once_with(*t.exc_info)

    def _TestReraise(self, reraise, callcnt, listener=False):
        with testhelpers.Patcher(sys, 'stderr') as mp:
            t = self.newthread(reraise=reraise)
            if listener:
                t.excepted.connect(lambda *_: None)
            t.start()
            self.assertRaises(NotImplementedError, threadutils.join_timeout, t)
        self.assertEqual(
            mp.newvalue.write.call_count, callcnt,
            'stderr.write should have been called %s times, '
            'was called %s times with the following calls: %s' % (
                callcnt,
                mp.newvalue.write.call_count,
                mp.newvalue.write.call_args_list))

    def testStdErrWrittenIfReraiseNoneAndNoListenerOrExcepthook(self):
        self._TestReraise(None, 1)

    def testStdErrNotWrittenIfReraiseNoneAndHasListener(self):
        self._TestReraise(None, 0, True)

    def testStdErrNotWrittenIfReraiseNoneAndCustomExcepthook(self):
        with testhelpers.Patcher(sys, 'excepthook'):
            self._TestReraise(None, 0)

    def testStdErrWrittenIfReraiseTrue(self):
        # Install hook and listener to avoid raise,
        # make sure reraise respected.
        with testhelpers.Patcher(sys, 'excepthook'):
            self._TestReraise(True, 1, True)

    def testStdErrNotWrittenIfReraiseFalse(self):
        self._TestReraise(False, 0)


class TestNotAThread(unittest.TestCase):
    def testRunsSync(self):
        a = []
        threadutils.NotAThread(target=a.append, args=('a',)).start()
        self.assertEqual(a, ['a'])

    def testWithRaise(self):
        def raiseit():
            raise NotImplementedError()
        self.assertRaises(NotImplementedError,
                          threadutils.NotAThread(target=raiseit).start)

    def testJoinReturns(self):
        t = threadutils.NotAThread()
        t.start()
        t.join()

    def testJoinRaisesIfNotStarted(self):
        t = threadutils.NotAThread()
        self.assertRaises(RuntimeError, t.join)


class TestTimerExt(unittest.TestCase):

    def _startTimer(self, interval):
        self.timediff = None

        def callback():
            self.timediff = time.time() - self.stime
        t = threadutils.TimerExt(interval, callback)
        t.start()
        self.stime = time.time()
        return t

    def testFires(self):
        interval = 0.02
        t = self._startTimer(interval)
        time.sleep(interval * 1.1)
        for i in range(10):
            if not t.isAlive():
                break
            time.sleep(interval * .2)
        self.assertFalse(t.isAlive())
        testhelpers.assertBetween(self, interval * .1, self.timediff, interval * 4)

    def testInvalidArgs(self):
        cb = lambda: 1
        self.assertRaises(ValueError, threadutils.TimerExt, 0, cb)
        self.assertRaises(TypeError, threadutils.TimerExt, None, cb)
        self.assertRaises(ValueError, threadutils.TimerExt, -0.1, cb)
        self.assertRaises(ValueError, threadutils.TimerExt, 0.1, None)

    def testResetFailsIfRun(self):
        t = self._startTimer(0.001)
        threadutils.join_timeout(t)
        self.assertRaises(RuntimeError, t.restart)

    def testResetWorks(self):
        interval = 0.02
        halfinterval = interval / 2
        t = self._startTimer(interval)
        time.sleep(halfinterval)
        t.restart()
        self.assertTrue(t.isAlive())
        threadutils.join_timeout(t)
        # A compare doesn't work- timing issues make it unreliable.
        # Just ensure we have a time diff within some acceptable threshold.
        testhelpers.assertBetween(self, interval, self.timediff, interval * 4)

    def testMultipleResets(self):
        """Tests resetting multiple times works."""
        t = self._startTimer(.05)
        t.restart()
        t.restart()
        t.restart()
        t.restart()

        # Uncomment this to make sure float and timing errors don't effect
        # our tests.
        #    def testItALot(self):
        #        for _ in xrange(100):
        #            self.testFires()
        #            self.testResetWorks()
        #


class TestToken(unittest.TestCase):
    def testAll(self):
        """Basic functionality test."""
        t = threadutils.Token()
        self.assertFalse(t.is_set())
        t.set()
        self.assertTrue(t.is_set())


class TestMemoize(unittest.TestCase):

    def testNoRecalc(self):
        """Test that memoizing doesn't recalculate."""
        li = []

        @threadutils.memoize
        def foo():
            li.append(0)
        foo()
        self.assertEqual([0], li)
        foo()
        self.assertEqual([0], li)

    def testRaiseIfParametersRequired(self):
        """Test that passing in a function requiring a parameter
        raises a ValueError."""
        self.assertRaises(ValueError, threadutils.memoize, lambda a: None)
        self.assertRaises(ValueError, threadutils.memoize, lambda a=1: None)

    def testAssertsIfPassedFuncAndUseLockIsTrue(self):
        self.assertRaises(AssertionError,
                          threadutils.memoize, lambda: None, True)

    def testLocksMemoize(self):
        """Creates several threads that all call the memoized function.

        We create a mock lock class to make sure all threads have hit our
        'lock', then we actually evaluate.
        """
        self.enteredLockCnt = 0
        numthreads = 4

        def lock():
            def enter(_):
                self.enteredLockCnt += 1
                while self.enteredLockCnt < numthreads:
                    time.sleep(0.01)
            inner = mock.Mock(__enter__=enter, __exit__=lambda *_: None)
            return inner
        li = []

        @threadutils.memoize(useLock=True, _lockcls=lock)
        def testit():
            self.assertEqual(self.enteredLockCnt, numthreads)
            li.append(0)
        threads = [threading.Thread(target=testit) for _ in range(numthreads)]
        map(threading.Thread.start, threads)
        map(threading.Thread.join, threads)
        self.assertEqual([0], li)


class TestExpiringMemoize(unittest.TestCase):

    def testCaches(self):
        now = [1]

        def gettime():
            return now[0]
        counter = [0]

        @threadutils.expiring_memoize(2, gettime)
        def func():
            counter[0] += 1
            return counter[0]
        self.assertEqual(func(), 1)
        self.assertEqual(func(), 1)
        now[0] = 100
        self.assertEqual(func(), 2)
