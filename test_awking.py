from unittest import TestCase

from io import StringIO
import re

from awking import RangeFilter, RangeCollector, RangeGrouper, QueueSink
from awking import ensure_predicate


class TestEnsurePredicate(TestCase):
    def test_string(self):
        predicate = ensure_predicate('^a')
        self.assertTrue(callable(predicate))

    def test_regexp(self):
        predicate = ensure_predicate(re.compile('^a'))
        self.assertTrue(callable(predicate))

    def test_function(self):
        def func(param):  # pylint: disable=unused-argument
            return True
        predicate = ensure_predicate(func)
        self.assertTrue(callable(predicate))

    def test_invalid(self):
        with self.assertRaises(TypeError):
            ensure_predicate(5)


class TestRangeFilter(TestCase):
    def test_one_range(self):
        output = []
        range_filter = RangeFilter(lambda x: x == 2, lambda x: x == 3,
                                   action=output.append)
        for i in [1, 2, 5, 3, 5]:
            range_filter(i)
        self.assertEqual([2, 5, 3], output)

    def test_two_ranges(self):
        output = []
        range_filter = RangeFilter(lambda x: x == 2, lambda x: x == 3,
                                   action=output.append)
        for i in [1, 2, 5, 3, 5, 2, 4, 4, 3]:
            range_filter(i)
        self.assertEqual([2, 5, 3, 2, 4, 4, 3], output)

    def test_regexp_as_string(self):
        output = StringIO()
        range_filter = RangeFilter('^a', '^b', action=output.write)
        for line in ['abc\n', 'abc\n', 'jvz\n', 'bbb\n', 'juq\n']:
            range_filter(line)
        self.assertEqual('abc\nabc\njvz\nbbb\n', output.getvalue())

    def test_double_start(self):
        output = []
        range_filter = RangeFilter(lambda x: x == 2, lambda x: x == 3,
                                   action=output.append)
        for i in [1, 2, 2, 3, 5, 2, 4, 4, 3]:
            range_filter(i)
        self.assertEqual([2, 2, 3, 2, 4, 4, 3], output)

    def test_double_end(self):
        output = []
        range_filter = RangeFilter(lambda x: x == 2, lambda x: x == 3,
                                   action=output.append)
        for i in [1, 2, 5, 3, 5, 3, 4, 4, 3]:
            range_filter(i)
        self.assertEqual([2, 5, 3], output)


class TestRangeCollector(TestCase):
    def test_one_range(self):
        collector = RangeCollector(lambda x: x == 2, lambda x: x == 3)
        with collector:
            for i in [1, 2, 5, 3, 5]:
                collector(i)
        self.assertEqual([[2, 5, 3]], collector.output)

    def test_two_ranges(self):
        collector = RangeCollector(lambda x: x == 2, lambda x: x == 3)
        with collector:
            for i in [1, 2, 5, 3, 5, 2, 4, 4, 3]:
                collector(i)
        self.assertEqual([[2, 5, 3], [2, 4, 4, 3]], collector.output)

    def test_regexp(self):
        collector = RangeCollector(re.compile('a'), re.compile('b'),
                                   sink_type=QueueSink)
        with collector:
            for line in 'xf ga zu jd bq zu aa qa gb'.split():
                collector(line)
        self.assertEqual([['ga', 'zu', 'jd', 'bq'], ['aa', 'qa', 'gb']],
                         [list(x) for x in collector.output])

    def test_double_start(self):
        collector = RangeCollector(lambda x: x == 2, lambda x: x == 3)
        with collector:
            for i in [1, 2, 2, 5, 3, 5, 2, 4, 4, 3]:
                collector(i)
        self.assertEqual([[2, 2, 5, 3], [2, 4, 4, 3]], collector.output)

    def test_double_end(self):
        collector = RangeCollector(lambda x: x == 2, lambda x: x == 3)
        with collector:
            for i in [1, 2, 5, 3, 3, 5, 2, 4, 4, 3]:
                collector(i)
        self.assertEqual([[2, 5, 3], [2, 4, 4, 3]], collector.output)


class TestRangeGrouper(TestCase):
    def test_one_group(self):
        grouper = RangeGrouper(lambda x: x == 2, lambda x: x == 3,
                               [1, 2, 5, 3, 5])
        self.assertEqual([[2, 5, 3]], [list(x) for x in grouper])

    def test_two_group(self):
        grouper = RangeGrouper(lambda x: x == 2, lambda x: x == 3,
                               [1, 2, 5, 3, 5, 2, 4, 4, 3])
        self.assertEqual([[2, 5, 3], [2, 4, 4, 3]],
                         [list(x) for x in grouper])

    def test_outer_iteration(self):
        grouper = RangeGrouper(lambda x: x == 2, lambda x: x == 3,
                               [1, 2, 5, 3, 5, 2, 4, 4, 3, 6])
        group1 = next(grouper)
        group2 = next(grouper)
        with self.assertRaises(StopIteration):
            next(grouper)
        self.assertEqual([2, 5, 3], list(group1))
        self.assertEqual([2, 4, 4, 3], list(group2))

    def test_regexp(self):
        grouper = RangeGrouper(re.compile('a'), re.compile('b'),
                               'xf ga zu jd bq zu aa qa gb'.split())
        self.assertEqual([['ga', 'zu', 'jd', 'bq'], ['aa', 'qa', 'gb']],
                         [list(x) for x in grouper])

    def test_double_start(self):
        grouper = RangeGrouper(lambda x: x == 2, lambda x: x == 3,
                               [1, 2, 2, 5, 3, 5, 2, 4, 4, 3])
        self.assertEqual([[2, 2, 5, 3], [2, 4, 4, 3]],
                         [list(x) for x in grouper])

    def test_double_end(self):
        grouper = RangeGrouper(lambda x: x == 2, lambda x: x == 3,
                               [1, 2, 5, 3, 3, 5, 2, 4, 4, 3])
        self.assertEqual([[2, 5, 3], [2, 4, 4, 3]],
                         [list(x) for x in grouper])
