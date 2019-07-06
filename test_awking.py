# pylint: disable=missing-docstring
from unittest import TestCase

import re

from awking import RangeGrouper, LazyRecord
from awking import _ensure_predicate, _make_columns, records


class TestEnsurePredicate(TestCase):
    def test_string(self):
        predicate = _ensure_predicate('^a')
        self.assertTrue(callable(predicate))

    def test_regexp(self):
        predicate = _ensure_predicate(re.compile('^a'))
        self.assertTrue(callable(predicate))

    def test_function(self):
        # noinspection PyUnusedLocal
        # pylint: disable=unused-argument
        def func(param):
            return True
        predicate = _ensure_predicate(func)
        self.assertTrue(callable(predicate))

    def test_invalid(self):
        with self.assertRaises(TypeError):
            _ensure_predicate(5)


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
            # noinspection PyStatementEffect
            # pylint: disable=pointless-statement
            record[3]

    def test_full_range(self):
        text = 'abc def jkzzz'
        record = LazyRecord(text, lambda x: x.split())
        self.assertEqual(['abc', 'def', 'jkzzz'], record[:])

    def test_str(self):
        text = 'abc def jkzzz'
        record = LazyRecord(text, lambda x: x.split())
        self.assertEqual(text, str(record))


class TestMakeColumns(TestCase):
    def test_one(self):
        self.assertEqual([(0, 5)], _make_columns([5]))

    def test_two(self):
        self.assertEqual([(0, 3), (3, 5)], _make_columns([3, 2]))

    def test_tail(self):
        self.assertEqual([(0, 3), (3, 5), (5, None)],
                         _make_columns([3, 2, ...]))


class TestRecords(TestCase):
    def test_blank(self):
        lines = ['abc def jkzzz']
        self.assertEqual(['abc', 'def', 'jkzzz'], next(records(lines))[:])

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

    def test_widths_with_tail(self):
        lines = ['abx-something--rrr']
        self.assertEqual(['abx', '-somet', 'hing--', 'rrr'],
                         next(records(lines, widths=[3, 6, 6, ...]))[:])

    def test_pattern(self):
        lines = ['abx-something--rrr']
        self.assertEqual(['abx', 'something', 'rrr'],
                         next(records(lines, pattern='[a-z]+'))[:])

    def test_pattern_regexp(self):
        lines = ['abx-something--rrr']
        self.assertEqual(['abx', 'something', 'rrr'],
                         next(records(lines, pattern=re.compile('[a-z]+')))[:])
