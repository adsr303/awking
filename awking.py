from collections.abc import Callable
from contextlib import closing
from queue import Queue, SimpleQueue, Empty
import re


def ensure_predicate(value):
    if isinstance(value, re.Pattern):
        return value.search
    elif isinstance(value, str):
        return re.compile(value).search
    elif isinstance(value, Callable):
        return value
    raise TypeError(type(value))


class Switchable:
    def __init__(self, predicate, action):
        self.predicate = predicate
        self.action = action
        self.opposite = None


class InsideFilter(Switchable):
    def __call__(self, input):
        self.action(input)
        if self.predicate(input):
            return self.opposite
        return self


class OutsideFilter(Switchable):
    def __call__(self, input):
        if self.predicate(input):
            self.action(input)
            return self.opposite
        return self


class RangeFilter:
    def __init__(self, first, last, *, action=print):
        first = ensure_predicate(first)
        last = ensure_predicate(last)
        outside = OutsideFilter(first, action)
        inside = InsideFilter(last, action)
        inside.opposite = outside
        outside.opposite = inside
        self.action = outside

    def __call__(self, input):
        self.action = self.action(input)


class ListSink:
    def __init__(self, first, last):
        self.first = first
        self.last = last
        self.output = []
        self.current = None

    def __call__(self, input):
        if self.first(input) and self.current is None:
            self.current = []
            self.output.append(self.current)
        self.current.append(input)
        if self.last(input) and self.current is not None:
            self.current = None

    def close(self):
        self.current = None


POISON = object()


class IterableQueue(Queue):
    def __iter__(self):
        while True:
            item = self.get()
            if item is POISON:
                break
            yield item

    def close(self):
        self.put(POISON)


class QueueSink:
    def __init__(self, first, last):
        self.first = first
        self.last = last
        self.output = IterableQueue()
        self.current = None

    def __call__(self, input):
        if self.first(input) and self.current is None:
            self.current = IterableQueue()
            self.output.put(self.current)
        self.current.put(input)
        if self.last(input) and self.current is not None:
            self.current.close()
            self.current = None

    def __del__(self):
        self.close()

    def close(self):
        self.output.close()
        if self.current is not None:
            self.current.close()
            self.current = None


class RangeCollector:
    def __init__(self, first, last, *, sink_type=ListSink):
        first = ensure_predicate(first)
        last = ensure_predicate(last)
        self.sink = sink_type(first, last)
        self.filter = RangeFilter(first, last, action=self.sink)

    def __call__(self, input):
        self.filter(input)

    def __del__(self):
        self.close()

    def __enter__(self):
        return closing(self)

    def __exit__(self, *exc):
        self.close()

    def close(self):
        self.sink.close()

    @property
    def output(self):
        return self.sink.output


class EndOfRange(Exception):
    pass


class RangeItem:
    def __init__(self, producer):
        self.producer = producer
        self.cache = SimpleQueue()

    def __iter__(self):
        while True:
            try:
                yield self.cache.get_nowait()
            except Empty:
                try:
                    yield self.producer.advance()
                except EndOfRange:
                    return


class RangeProducer:
    def __init__(self, first, last, input):
        self.first = ensure_predicate(first)
        self.last = ensure_predicate(last)
        self.input = iter(input)
        self.current = None

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                item = next(self.input)
            except StopIteration as e:
                raise StopIteration() from e
            if not self.current:
                if self.first(item):
                    self.current = RangeItem(self)
                    self.current.cache.put(item)
                    return self.current
                else:
                    continue
            else:
                self.current.cache.put(item)
                if self.last(item):
                    self.current = None

    def advance(self):
        if not self.current:
            raise EndOfRange()
        while True:
            try:
                item = next(self.input)
            except StopIteration as e:
                raise EndOfRange() from e
            if self.last(item):
                self.current = None
            return item
