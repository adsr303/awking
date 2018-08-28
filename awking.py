from collections import deque
from collections.abc import Callable
import re


def ensure_predicate(value):
    if isinstance(value, re.Pattern):
        return value.search
    if isinstance(value, str):
        return re.compile(value).search
    if isinstance(value, Callable):
        return value
    raise TypeError(type(value))


class EndOfGroup(Exception):
    pass


class Group:
    def __init__(self, grouper):
        self.grouper = grouper
        self.cache = deque()

    def __iter__(self):
        while True:
            try:
                yield self.cache.popleft()
            except IndexError:
                try:
                    yield self.grouper.next_item()
                except EndOfGroup:
                    return

    def append(self, item):
        self.cache.append(item)


class RangeGrouper:
    def __init__(self, first, last, iterable):
        self.first = ensure_predicate(first)
        self.last = ensure_predicate(last)
        self.iterable = iter(iterable)
        self.current = None

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                item = next(self.iterable)
            except StopIteration:
                raise StopIteration()
            # pylint: disable=no-else-return
            if not self.current:
                if self.first(item):
                    group = Group(self)
                    self.current = group
                    self.push_to_current(item)
                    return group
                else:
                    continue
            else:
                self.push_to_current(item)

    def push_to_current(self, item):
        self.current.append(item)
        if self.last(item):
            self.current = None

    def next_item(self):
        if not self.current:
            raise EndOfGroup()
        while True:
            try:
                item = next(self.iterable)
            except StopIteration:
                raise EndOfGroup()
            if self.last(item):
                self.current = None
            return item
