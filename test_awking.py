from unittest import TestCase

import re

from awking import RangeGrouper, records, LazyRecord, ensure_predicate


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


class TestRangeGrouper(TestCase):
    def test_one_group(self):
        grouper = RangeGrouper(lambda x: x == 2, lambda x: x == 3,
                               [1, 2, 5, 3, 5])
        self.assertEqual([[2, 5, 3]], [list(x) for x in grouper])

    def test_two_groups(self):
        grouper = RangeGrouper(lambda x: x == 2, lambda x: x == 3,
                               [1, 2, 5, 3, 5, 2, 4, 4, 3])
        self.assertEqual([[2, 5, 3], [2, 4, 4, 3]],
                         [list(x) for x in grouper])

    def test_no_match(self):
        grouper = RangeGrouper(lambda x: x == 2, lambda x: x == 3,
                               [1, 4, 0, 1])
        self.assertEqual([], [list(x) for x in grouper])

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

    def test_one_item_group(self):
        grouper = RangeGrouper(lambda x: x == 2, lambda x: x % 2 == 0,
                               [1, 2, 5, 3, 3, 5, 4, 3])
        self.assertEqual([[2]], [list(x) for x in grouper])

    def test_truncated_last_group(self):
        grouper = RangeGrouper(lambda x: x == 2, lambda x: x == 3,
                               [1, 2, 5, 3, 3, 5, 2, 4, 4])
        self.assertEqual([[2, 5, 3], [2, 4, 4]],
                         [list(x) for x in grouper])


class TestLazyRecord(TestCase):
    def test_ellipsis(self):
        text = 'abc def jkzzz'
        record = LazyRecord(text, lambda x: x.split())
        self.assertEqual(text, record[...])

    def test_numerical_indices(self):
        text = 'abc def jkzzz'
        record = LazyRecord(text, lambda x: x.split())
        self.assertEqual(('abc', 'jkzzz', 'jkzzz'),
                         (record[0], record[2], record[-1]))

    def test_out_of_range(self):
        text = 'abc def jkzzz'
        record = LazyRecord(text, lambda x: x.split())
        self.assertEqual(3, len(record))
        with self.assertRaises(IndexError):
            record[3]

    def test_full_range(self):
        text = 'abc def jkzzz'
        record = LazyRecord(text, lambda x: x.split())
        self.assertEqual(['abc', 'def', 'jkzzz'], record[:])

    def test_str(self):
        text = 'abc def jkzzz'
        record = LazyRecord(text, lambda x: x.split())
        self.assertEqual(text, str(record))


class TestRecords(TestCase):
    def test_blank(self):
        lines = ['abc def jkzzz']
        self.assertEquals(['abc', 'def', 'jkzzz'], next(records(lines))[:])

    def test_separator(self):
        lines = ['abx-something--rrr']
        self.assertEqual(['abx', 'something', '', 'rrr'],
                         next(records(lines, separator='-'))[:])

    def test_regexp(self):
        lines = ['abx-something--rrr']
        self.assertEqual(['abx', 'something', 'rrr'],
                         next(records(lines, separator=re.compile('-+')))[:])

    def test_widths(self):
        lines = ['abx-something--rrr']
        self.assertEqual(['abx', '-somet', 'hing--', 'rrr'],
                         next(records(lines, widths=[3, 6, 6, 3]))[:])
