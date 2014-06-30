import datetime
import unittest

import mock

from brennivin import itertoolsext as it


class TestBundle(unittest.TestCase):

    def testDotGetWorks(self):
        d = it.Bundle({'a': 1, 'b': 2})
        self.assertEqual(d.a, 1)
        self.assertEqual(d.b, 2)

    def testDotGetRaisesKeyError(self):
        """Tests a KeyError is raised when an attribute that
        is not a key is accessed."""
        b = it.Bundle()
        self.assertRaises(KeyError, lambda: b.foo)

    def testHiddenKeysReturnReal(self):
        """Tests that any keys that hide a dict attr will return the
        dict's attr, not the key value."""
        b = it.Bundle({'keys': 1})
        self.assertNotEqual(b.keys, 1)
        self.assertTrue(callable(b.keys))

    def testStr(self, func=str):
        b = it.Bundle({'keys': 1})
        ideal = "Bundle({'keys': 1})"
        self.assertEqual(func(b), ideal)

    def testRepr(self):
        self.testStr(repr)


class TestAll(unittest.TestCase):
    def testNoPredicate(self):
        self.assertTrue(it.all([1, True, -1, 'a']))
        self.assertFalse(it.all([1, 'a', None]))

    def testWithPredicate(self):
        isstr = lambda s: isinstance(s, str)
        self.assertTrue(it.all(['', 'a', 'abC'], isstr))
        self.assertFalse(it.any([False, None, True, 0L, 0.0], isstr))


class TestAny(unittest.TestCase):
    def testNoPredicate(self):
        self.assertTrue(it.any([False, 0, 1]))
        self.assertFalse(it.any([False, None, '', 0, 0L, 0.0]))

    def testWithPredicate(self):
        isstr = lambda s: isinstance(s, str)
        self.assertTrue(it.any([bool, 1, ''], isstr))
        self.assertFalse(it.any([False, None, 0.0], isstr))


class TestBucket(unittest.TestCase):
    def testsWillSort(self):
        """Tests basic functionality, and that the function correctly
        preserves input sequence value ordering."""
        inp = ('a', 1), ('b', 4), ('a', 2), ('b', 3)
        res = it.bucket(inp, lambda x: x[0], lambda x: x[1])
        ideal = {'a': [1, 2],
                 'b': [4, 3]}
        self.assertEqual(ideal, res)


class TestCount(unittest.TestCase):
    def testAll(self):
        self.assertEqual(3, it.count([1, 2, 3]))
        self.assertEqual(2, it.count([1, 2, 3, 4], predicate=lambda x: x > 2))
        self.assertEqual(3, it.count(iter([1, 2, 3])))


class TestDatespan(unittest.TestCase):
    def testAll(self):
        dt = datetime.datetime
        cnt = it.count
        self.assertEqual(60,
                         cnt(it.datespan(dt(2010, 2, 20), dt(2010, 4, 21))))
        self.assertEqual(30,
                         cnt(it.datespan(dt(2010, 2, 20), dt(2010, 4, 21),
                                         datetime.timedelta(days=2))))
        self.assertEqual(60,
                         cnt(it.datespan(dt(2010, 4, 21), dt(2010, 2, 20))))


class TestFirst(unittest.TestCase):
    def testAll(self):
        self.assertEqual(1, it.first([1, 2, 3]))
        self.assertEqual(3, it.first((1, 2, 3), lambda x: x > 2))
        self.assertRaises(StopIteration, it.first, [])


class TestFirstOrDefault(unittest.TestCase):
    def testAll(self):
        self.assertEqual(1, it.first_or_default([1, 2, 3]))
        self.assertEqual(3, it.first_or_default((1, 2, 3), lambda x: x > 2))
        self.assertEqual(it.first_or_default([], default=5), 5)
        self.assertFalse(it.first_or_default([1, 2, 3], lambda x: x > 4))


class TestFlatmap(unittest.TestCase):
    class Book(object):
        def __init__(self, *authors):
            self.authors = authors

    def setUp(self):
        self.books = [self.Book('a', 'b'), self.Book('c')]

    def testFlatmapReturnsFlatList(self):
        """Test that using Flatmap with a sequence of nested sequences
        result in a flat list."""
        allauthors = it.flatmap(lambda book: book.authors, self.books)
        knowngood = ['a', 'b', 'c']
        self.assertEqual(list(allauthors), knowngood)

    def testFlatmapFailsNonNestedList(self):
        """Test that passing Flatmap a sequence that does not contain nested
        iterables raises a TypeError."""
        data = [1, 2]
        iterator = it.flatmap(lambda e: e, data)
        self.assertRaises(TypeError, iterator.next)

    def testFlatmapWithNone(self):
        """Test that calling Flatmap with function as None results a
        TypeError."""
        result = it.flatmap(None, [1, 2, 3])
        self.assertRaises(TypeError, result.next)


class TestGroupBy(unittest.TestCase):
    def testsWillSort(self):
        """Tests basic functionality,
        and that the function will sort the input sequence according
        to the keyfunc."""
        inp = ('a', 1), ('b', 4), ('a', 2), ('b', 3)
        res = list(it.groupby2(inp, lambda x: x[0]))
        ideal = [('a', [('a', 1), ('a', 2)]),
                 ('b', [('b', 4), ('b', 3)])]
        self.assertEqual(ideal, res)


class TestGroupsOfN(unittest.TestCase):

    def testListIsGroupable(self):
        """Test that a list can be grouped."""
        v = [1, 2, 3, 2, 3, 4]
        ideal = [[1, 2, 3], [2, 3, 4]]
        result = it.groups_of_n(v, 3)
        self.assertEqual(result, ideal)

    def testBadSizeRaises(self):
        """Test that a list of bad length raises error."""
        v = [1, 2, 3, 4]
        self.assertRaises(ArithmeticError, it.groups_of_n, v, 3)


class TestLast(unittest.TestCase):
    def testAll(self):
        self.assertEqual(5, it.last([1, 8, 4, 5]))
        self.assertEqual(4, it.last([1, 8, 4, 5], lambda x: x != 5))
        self.assertEqual(None, it.last([1, 5, None], lambda x: x != 5))
        self.assertRaises(StopIteration, it.last, [])
        self.assertRaises(StopIteration, it.last, [1, 2, 3], lambda x: x > 5)


class TestLastOrDefault(unittest.TestCase):
    def testAll(self):
        self.assertEqual(5, it.last_or_default([1, 8, 4, 5]))
        self.assertEqual(4, it.last_or_default([1, 8, 4, 5], lambda x: x != 5))
        self.assertIsNone(it.last_or_default([]))
        self.assertIsNone(it.last_or_default([1, 2, 3], lambda x: x > 5))


class TestSingle(unittest.TestCase):
    def testEmpty(self):
        """Test that a StopIteration is raised for an empty sequence."""
        self.assertRaises(StopIteration, it.single, [])

    def testMultiple(self):
        """Test a StopIteration is raised for a sequence of
        more than one item."""
        self.assertRaises(StopIteration, it.single, [1, 2])

    def testSingle(self):
        """Test that the single collection value is returned."""
        self.assertEqual('a', it.single(['a']))


class TestSkip(unittest.TestCase):
    def testSkips(self):
        res = list(it.skip(xrange(20), 10))
        self.assertEqual(range(10, 20), res)

    def testCountExceedsLength(self):
        """Tests that a skip number higher than the length of the enumerable
        returns an empty iterator."""
        res = list(it.skip(range(5), 20))
        self.assertFalse(res)

    def testBehavesSameAsSlice(self):
        enum = range(10)
        res = list(it.skip(enum, 5))
        sliced = enum[5:]
        self.assertEqual(res, sliced)


class TestTake(unittest.TestCase):
    def t(self, *args, **kwargs):
        return list(it.take(*args, **kwargs))

    def testIsGenerator(self):
        self.assertTrue(hasattr(it.take([1], 1), 'next'))

    def testAll(self):
        self.assertEqual([2, 5], self.t([2, 5, 1, 3], 2))
        self.assertEqual([1, 2, 3], self.t([1, 2, 3], 5))

    def testWithPredicate(self):
        self.assertEqual([2, 3], self.t([1, 2, 3, 4], 2, lambda x: x > 1))

    def testWithZero(self):
        self.assertEqual([], self.t([1, 2, 3], 0))

    def testRaisesIfNumberIsNotNumber(self):
        self.assertRaises(TypeError, self.t, [], '1')


class TestUnique(unittest.TestCase):
    def testAll(self):
        self.assertEqual(['a', 'b', 'c'],
                         list(it.unique(['a', 'b', 'c', 'b'])))
        un = it.unique([{'a': 1, 'b': 2}, {'a': 1, 'b': 2}], lambda x: x['a'])
        self.assertEqual([{'a': 1, 'b': 2}], list(un))


class TreeTester:

    def __init__(self, name, *children):
        self.name = str(name)
        self.children = lambda: children

    def __repr__(self):
        return 'Node: ' + self.name

    def getChild(self, ind):
        return self.children()[ind]


def createTree():
    """
    n1  n2  n4
            n5
        n3
    """
    n5 = TreeTester(5)
    n4 = TreeTester(4)
    n3 = TreeTester(3)
    n2 = TreeTester(2, n4, n5)
    n1 = TreeTester(1, n2, n3)
    return n1, n2, n3, n4, n5


class TestYieldDF(unittest.TestCase):

    def testIsDepthFirst(self):
        """Test that the depth first sort returns as expected."""
        n1, n2, n3, n4, n5 = createTree()
        ordered = n2, n4, n5, n3
        val = tuple(it.treeyield_depthfirst(n1, lambda n: n.children()))
        self.assertEqual(val, ordered)

    def testYieldRootReturnsRoot(self):
        """Test that the yieldRoot function yields the root or not."""
        n1, n2, n3, n4, n5 = createTree()
        val = tuple(it.treeyield_depthfirst(n1, lambda n: n.children()))
        self.assertEqual(val, (n2, n4, n5, n3))  # Test without
        val = tuple(it.treeyield_depthfirst(
            n1, lambda n: n.children(), yieldnode=True))
        self.assertEqual(val, (n1, n2, n4, n5, n3))

    def testGetChild(self):
        """Test that the getChild argument is called with proper parameters
        and yields the correct result."""
        n1, n2, n3, n4, n5 = createTree()
        val = tuple(it.treeyield_depthfirst(
            n1,
            lambda n: len(n.children()),
            lambda node, arg: node.getChild(arg)))
        self.assertEqual(val, (n2, n4, n5, n3))


class TestYieldBF(unittest.TestCase):

    def testIsBreadthFirst(self):
        """Test that the depth first sort returns as expected."""
        n1, n2, n3, n4, n5 = createTree()
        ordered = n2, n3, n4, n5
        val = tuple(it.treeyield_breadthfirst(n1, lambda n: n.children()))
        self.assertEqual(val, ordered)

    def testYieldRootReturnsRoot(self):
        """Test that the yieldRoot function yields the root or not."""
        n1, n2, n3, n4, n5 = createTree()
        val = tuple(it.treeyield_breadthfirst(n1, lambda n: n.children()))
        self.assertEqual(val, (n2, n3, n4, n5))  # Test without
        val = tuple(it.treeyield_breadthfirst(
            n1, lambda n: n.children(), yieldnode=True))
        self.assertEqual(val, (n1, n2, n3, n4, n5))

    def testGetChild(self):
        """Test that the getChild argument is called with proper parameters
        and yields the correct result."""
        n1, n2, n3, n4, n5 = createTree()
        val = tuple(it.treeyield_breadthfirst(
            n1,
            lambda n: len(n.children()),
            lambda node, arg: node.getChild(arg)))
        self.assertEqual(val, (n2, n3, n4, n5))


class TestCompoundGetSet(unittest.TestCase):

    def testGetCompoundItem(self):
        """Test that GetCompoundItem correctly gets keys in collections."""
        res = it.get_compound_item(['a', 'b'], 0)
        self.assertEqual(res, 'a')

        res = it.get_compound_item(
            ['a', 'b', {'c': ['d', {'e': True}]}],
            2,
            'c', 1, 'e')
        self.assertEqual(res, True)

    def testSetCompoundItem(self):
        """Test that SetCompoundItem correctly sets keys in collections."""
        coll = ['a', 'b']
        it.set_compound_item(coll, True, 0)
        self.assertEqual(coll, [True, 'b'])

        coll = ['a', 'b', {'c': ['d', {'e': False}]}]
        it.set_compound_item(coll, True, 2, 'c', 1, 'e')
        self.assertEqual(coll, ['a', 'b', {'c': ['d', {'e': True}]}])


class TestCompoundDeletion(unittest.TestCase):
    def testDeletingListElement(self):
        d = ['a', 'b']
        it.del_compound_item(d, 1)
        self.assertEqual(d, ['a'])

    def testDeletingDict(self):
        d = ['a', {'b': 'value'}]
        it.del_compound_item(d, 1)
        self.assertEqual(d, ['a'])

    def testDeletingKeyFromDict(self):
        d = ['a', {'b': 'value'}]
        it.del_compound_item(d, 1, 'b')
        self.assertEqual(d, ['a', {}])


class TestCompoundAttrGetAndSet(unittest.TestCase):

    def getObject(self):
        obj = it.Bundle()
        obj.alist = [
            it.Bundle({'spam': 'eggs'})
        ]
        return obj

    def testGetAttr(self):
        self.assertEqual('eggs', it.get_compound_attr(
            self.getObject(), *['alist', 0, 'spam']))

    def testErrorGettingBadPath(self):
        self.assertRaises(IndexError, it.get_compound_attr,
                          self.getObject(), *['alist', 1])

    def testSetAttr(self):
        obj = self.getObject()
        self.assertEqual('eggs', obj.alist[0].spam)
        it.set_compound_attr(obj, 'bar', *['alist', 0, 'spam'])
        ideal = 'bar'
        self.assertEqual(ideal, obj.alist[0].spam, "Attr '%s' not set on <%s>"
                                                   % (ideal, obj))


class TestFrozenDict(unittest.TestCase):

    def testRaisesOnMutation(self):
        d = it.FrozenDict(a='b', **{'x': 'y'})
        try:
            d['p'] = 'q'
            self.fail('Should have raised')
        except TypeError:
            pass
        self.assertRaises(TypeError, d.__setitem__, 'p', 'q')
        self.assertRaises(TypeError, d.clear)
        self.assertRaises(TypeError, d.pop, 'a')
        self.assertRaises(TypeError, d.popitem)
        self.assertRaises(TypeError, d.setdefault, 'p', 'q')
        try:
            del d['a']
            self.fail('Should have raised')
        except TypeError:
            pass
        self.assertRaises(TypeError, d.__delitem__, 'a')

    def testEmpty(self):
        d = it.FrozenDict()
        self.assertFalse(d)

    def testAccessors(self):
        d = it.FrozenDict(a='b', x='y', **{'p': 'q'})
        self.assertEqual(d.get('a'), 'b')
        self.assertEqual(d['x'], 'y')
        self.assertEqual(sorted(d.keys()), ['a', 'p', 'x'])
        self.assertIn('a', d)

    def testIsHashable(self):
        self.assertRaises(TypeError, hash, {})
        self.assertFalse(hash(it.FrozenDict()))
        self.assertTrue(hash(it.FrozenDict(a=1)))

    def testComparesWithDict(self):
        fd = it.FrozenDict(a=1)
        d = dict(a=1)
        self.assertEqual(fd, d)


class TestDictAdd(unittest.TestCase):
    def setUp(self):
        self.dict_base_a = {101: 101,
                            202: 202,
                            '303': 303,
                            (4, 0, 4): 404}
        self.dict_base_b = {101: 10,
                            '303': 30,
                            (4, 0, 4): 40,
                            505: 50}

    def test_dict_add(self):
        dict_a = self.dict_base_a.copy()
        it.dict_add(dict_a, self.dict_base_b)
        self.assertEqual(dict_a, {101: 111,
                                  202: 202,
                                  '303': 333,
                                  (4, 0, 4): 444,
                                  505: 50})

    def test_dict_multiply(self):
        dict_a = self.dict_base_a.copy()
        it.dict_add(dict_a, self.dict_base_b, lambda a, b: a * b)
        self.assertEqual(dict_a, {101: 1010,
                                  202: 202,
                                  '303': 9090,
                                  (4, 0, 4): 16160,
                                  505: 50})


class TestShuffle(unittest.TestCase):

    def testWithNone(self):
        """Test that Shuffle raises if collection is None."""
        self.assertRaises(TypeError, it.shuffle, None)

    def testReturnsCopy(self):
        """Test that Shuffle returns a copy,
        even if passed an empty or single item collection."""
        li = []
        self.assertNotEqual(id(it.shuffle(li)), id(li))
        li.append(1)
        self.assertNotEqual(id(it.shuffle(li)), id(li))

    def testShuffles(self):
        """Test that Shuffle actually shuffles."""
        li = range(0, 50)
        self.assertNotEqual(it.shuffle(li), li)
        self.assertNotEqual(it.shuffle(li), li)
        self.assertNotEqual(it.shuffle(li), li)
        self.assertNotEqual(it.shuffle(li), li)
        self.assertNotEqual(it.shuffle(li), li)
        self.assertNotEqual(it.shuffle(li), li)

    def testMaxAttemptsRaises(self):
        items = [1, 2, 3]
        with mock.patch('random.shuffle', mock.Mock(return_value=items)):
            self.assertRaises(AssertionError, it.shuffle, items, 1)
