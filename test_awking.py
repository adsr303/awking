from unittest import TestCase

from io import StringIO
import re

from awking import RangeFilter, RangeCollector, RangeProducer, QueueSink


class TestRangeFilter(TestCase):
    def test_one_range(self):
        output = []
        filter = RangeFilter(lambda x: x == 2, lambda x: x == 3,
                             action=output.append)
        for i in [1, 2, 5, 3, 5]:
            filter(i)
        self.assertEqual([2, 5, 3], output)

    def test_two_ranges(self):
        output = []
        filter = RangeFilter(lambda x: x == 2, lambda x: x == 3,
                             action=output.append)
        for i in [1, 2, 5, 3, 5, 2, 4, 4, 3]:
            filter(i)
        self.assertEqual([2, 5, 3, 2, 4, 4, 3], output)

    def test_regexp_as_string(self):
        output = StringIO()
        filter = RangeFilter('^a', '^b', action=output.write)
        for line in ['abc\n', 'abc\n', 'jvz\n', 'bbb\n', 'juq\n']:
            filter(line)
        self.assertEqual('abc\nabc\njvz\nbbb\n', output.getvalue())

    def test_double_start(self):
        output = []
        filter = RangeFilter(lambda x: x == 2, lambda x: x == 3,
                             action=output.append)
        for i in [1, 2, 2, 3, 5, 2, 4, 4, 3]:
            filter(i)
        self.assertEqual([2, 2, 3, 2, 4, 4, 3], output)

    def test_double_end(self):
        output = []
        filter = RangeFilter(lambda x: x == 2, lambda x: x == 3,
                             action=output.append)
        for i in [1, 2, 5, 3, 5, 3, 4, 4, 3]:
            filter(i)
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


class TestRangeProducer(TestCase):
    def test_one_range(self):
        producer = RangeProducer(lambda x: x == 2, lambda x: x == 3,
                                 [1, 2, 5, 3, 5])
        self.assertEqual([[2, 5, 3]], [list(x) for x in producer])

    def test_two_ranges(self):
        producer = RangeProducer(lambda x: x == 2, lambda x: x == 3,
                                 [1, 2, 5, 3, 5, 2, 4, 4, 3])
        self.assertEqual([[2, 5, 3], [2, 4, 4, 3]],
                         [list(x) for x in producer])

    def test_outer_iteration(self):
        producer = RangeProducer(lambda x: x == 2, lambda x: x == 3,
                                 [1, 2, 5, 3, 5, 2, 4, 4, 3, 6])
        range1 = next(producer)
        range2 = next(producer)
        with self.assertRaises(StopIteration):
            next(producer)
        self.assertEqual([2, 5, 3], list(range1))
        self.assertEqual([2, 4, 4, 3], list(range2))

    def test_regexp(self):
        producer = RangeProducer(re.compile('a'), re.compile('b'),
                                 'xf ga zu jd bq zu aa qa gb'.split())
        self.assertEqual([['ga', 'zu', 'jd', 'bq'], ['aa', 'qa', 'gb']],
                         [list(x) for x in producer])

    def test_double_start(self):
        producer = RangeProducer(lambda x: x == 2, lambda x: x == 3,
                                 [1, 2, 2, 5, 3, 5, 2, 4, 4, 3])
        self.assertEqual([[2, 2, 5, 3], [2, 4, 4, 3]],
                         [list(x) for x in producer])

    def test_double_end(self):
        producer = RangeProducer(lambda x: x == 2, lambda x: x == 3,
                                 [1, 2, 5, 3, 3, 5, 2, 4, 4, 3])
        self.assertEqual([[2, 5, 3], [2, 4, 4, 3]],
                         [list(x) for x in producer])
