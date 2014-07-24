import contextlib
import unittest
from random import choice

from brennivin import functoolsext


# noinspection PyShadowingNames
class TestLRU(unittest.TestCase):

    def assertCacheInfo(self, fib, **cikwargs):
        self.assertEqual(
            fib.cache_info(),
            functoolsext._CacheInfo(**cikwargs))

    def test_lru(self):
        def orig(x, y):
            return 3 * x + y
        f = functoolsext.lru_cache(maxsize=20)(orig)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(maxsize, 20)
        self.assertEqual(currsize, 0)
        self.assertEqual(hits, 0)
        self.assertEqual(misses, 0)

        domain = range(5)
        for i in range(1000):
            x, y = choice(domain), choice(domain)
            actual = f(x, y)
            expected = orig(x, y)
            self.assertEqual(actual, expected)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertTrue(hits > misses)
        self.assertEqual(hits + misses, 1000)
        self.assertEqual(currsize, 20)

        f.cache_clear()   # test clearing
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 0)
        self.assertEqual(misses, 0)
        self.assertEqual(currsize, 0)
        # noinspection PyUnboundLocalVariable
        f(x, y)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 0)
        self.assertEqual(misses, 1)
        self.assertEqual(currsize, 1)

        # Test bypassing the cache
        self.assertIs(f.__wrapped__, orig)
        f.__wrapped__(x, y)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 0)
        self.assertEqual(misses, 1)
        self.assertEqual(currsize, 1)

        f_cnt = [0]

        # test size zero (which means "never-cache")
        @functoolsext.lru_cache(0)
        def f():
            f_cnt[0] += 1
            return 20
        self.assertEqual(f.cache_info().maxsize, 0)
        for i in range(5):
            self.assertEqual(f(), 20)
        self.assertEqual(f_cnt[0], 5)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 0)
        self.assertEqual(misses, 5)
        self.assertEqual(currsize, 0)

        f_cnt = [0]

        # test size one
        @functoolsext.lru_cache(1)
        def f():
            f_cnt[0] += 1
            return 20
        self.assertEqual(f.cache_info().maxsize, 1)
        for i in range(5):
            self.assertEqual(f(), 20)
        self.assertEqual(f_cnt[0], 1)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 4)
        self.assertEqual(misses, 1)
        self.assertEqual(currsize, 1)

        f_cnt = [0]

        # test size two
        @functoolsext.lru_cache(2)
        def f(x):
            f_cnt[0] += 1
            return x * 10
        self.assertEqual(f.cache_info().maxsize, 2)
        for x in 7, 9, 7, 9, 7, 9, 8, 8, 8, 9, 9, 9, 8, 8, 8, 7:
            #    *  *              *                          *
            self.assertEqual(f(x), x * 10)
        self.assertEqual(f_cnt[0], 4)
        hits, misses, maxsize, currsize = f.cache_info()
        self.assertEqual(hits, 12)
        self.assertEqual(misses, 4)
        self.assertEqual(currsize, 2)

    def test_lru_with_maxsize_none(self):
        @functoolsext.lru_cache(maxsize=None)
        def fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)
        self.assertEqual(
            [fib(n) for n in range(16)],
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610])
        self.assertCacheInfo(
            fib, hits=28, misses=16, maxsize=None, currsize=16)
        fib.cache_clear()
        self.assertCacheInfo(fib, hits=0, misses=0, maxsize=None, currsize=0)

    def test_lru_with_exceptions(self):
        # Verify that user_function exceptions get passed through without
        # creating a hard-to-read chained exception.
        # http://bugs.python.org/issue13177
        for maxsize in (None, 128):
            @functoolsext.lru_cache(maxsize)
            def func(i):
                return 'abc'[i]
            self.assertEqual(func(0), 'a')
            with self.assertRaises(IndexError):
                func(15)
            # Verify that the previous exception did not result in a cached entry
            with self.assertRaises(IndexError):
                func(15)

    def test_lru_with_types(self):
        for maxsize in (None, 128):
            @functoolsext.lru_cache(maxsize=maxsize, typed=True)
            def square(x):
                return x * x
            self.assertEqual(square(3), 9)
            self.assertEqual(type(square(3)), type(9))
            self.assertEqual(square(3.0), 9.0)
            self.assertEqual(type(square(3.0)), type(9.0))
            self.assertEqual(square(x=3), 9)
            self.assertEqual(type(square(x=3)), type(9))
            self.assertEqual(square(x=3.0), 9.0)
            self.assertEqual(type(square(x=3.0)), type(9.0))
            self.assertEqual(square.cache_info().hits, 4)
            self.assertEqual(square.cache_info().misses, 4)

    def test_lru_with_keyword_args(self):
        @functoolsext.lru_cache()
        def fib(n):
            if n < 2:
                return n
            return fib(n=n - 1) + fib(n=n - 2)
        self.assertEqual(
            [fib(n=number) for number in range(16)],
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]
        )
        self.assertCacheInfo(fib, hits=28, misses=16, maxsize=128, currsize=16)
        fib.cache_clear()
        self.assertCacheInfo(fib, hits=0, misses=0, maxsize=128, currsize=0)

    def test_lru_with_keyword_args_maxsize_none(self):
        @functoolsext.lru_cache(maxsize=None)
        def fib(n):
            if n < 2:
                return n
            return fib(n=n - 1) + fib(n=n - 2)
        self.assertEqual(
            [fib(n=number) for number in range(16)],
            [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610])
        self.assertCacheInfo(
            fib, hits=28, misses=16, maxsize=None, currsize=16)
        fib.cache_clear()
        self.assertCacheInfo(fib, hits=0, misses=0, maxsize=None, currsize=0)

    def test_need_for_rlock(self):
        # This will deadlock on an LRU cache that uses a regular lock

        @functoolsext.lru_cache(maxsize=10)
        def test_func(x):
            """Used to demonstrate a reentrant lru_cache call
            within a single thread"""
            return x

        class DoubleEq:
            """Demonstrate a reentrant lru_cache call within a single thread"""
            def __init__(self, x):
                self.x = x

            def __hash__(self):
                return self.x

            def __eq__(self, other):
                if self.x == 2:
                    test_func(DoubleEq(1))
                return self.x == other.x

        test_func(DoubleEq(1))  # Load the cache
        test_func(DoubleEq(2))  # Load the cache
        self.assertEqual(
            test_func(DoubleEq(2)),  # Trigger a re-entrant __eq__ call
            DoubleEq(2))  # Verify the correct return value


class LooseContextManagerTests(unittest.TestCase):

    # noinspection PyUnresolvedReferences
    def test_is_loose(self):
        @contextlib.contextmanager
        def strict():
            yield
        strict = strict()

        @functoolsext.loosecontextmanager
        def loose():
            yield
        loose = loose()

        strict.__enter__()
        with self.assertRaises(TypeError):
            strict.__exit__()

        loose.__enter__()
        loose.__exit__()
