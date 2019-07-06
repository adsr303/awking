"""Make it easier to use Python as an AWK replacement."""

from collections import deque
from collections.abc import Callable
from functools import partial
import re


def _ensure_predicate(value):
    if isinstance(value, Callable):
        return value
    if isinstance(value, str):
        return re.compile(value).search
    if isinstance(value, re.Pattern):
        return value.search
    raise TypeError(type(value))


class _EndOfGroup(Exception):
    pass


class _Group:
    def __init__(self, grouper):
        self.grouper = grouper
        self.cache = deque()

    def __iter__(self):
        while True:
            try:
                yield self.cache.popleft()
            except IndexError:
                try:
                    # pylint: disable=protected-access
                    # noinspection PyProtectedMember
                    yield self.grouper._next_item()
                except _EndOfGroup:
                    return

    def append(self, item):  # pylint: disable=missing-docstring
        self.cache.append(item)


class RangeGrouper:
    """Groups items from an iterable using start/end predicates.

    Each group is an iterator itself. Only as much input as needed is
    consumed from the iterable.
    """

    def __init__(self, begin, end, iterable):
        self.begin = _ensure_predicate(begin)
        self.end = _ensure_predicate(end)
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
                if self.begin(item):
                    group = _Group(self)
                    self.current = group
                    self._push_to_current(item)
                    return group
                else:
                    continue
            else:
                self._push_to_current(item)

    def _push_to_current(self, item):
        self.current.append(item)
        if self.end(item):
            self.current = None

    def _next_item(self):
        if not self.current:
            raise _EndOfGroup()
        while True:
            try:
                item = next(self.iterable)
            except StopIteration:
                raise _EndOfGroup()
            if self.end(item):
                self.current = None
            return item


class LazyRecord:
    """A list of logical fields found in text.

    Fields are extracted from `text` by applying `split`. A special
    index `...` (Ellipsis) can be used to retrieve the entire text.

    >>> r = LazyRecord('a bb ccc', lambda text: text.split())
    >>> r[0]       # AWK: $1
    'a'
    >>> r[-1]      # AWK: $NF
    'ccc'
    >>> r[...]     # AWK: $0
    'a bb ccc'
    >>> len(r)     # AWK: NF
    3

    The actual splitting is only done once actually needed (hence the
    class name).
    """

    def __init__(self, text, split):
        self.text = text
        self.fields = None
        self.split = split

    def __getitem__(self, index):
        if index is Ellipsis:
            return self.text
        self._ensure_split()
        return self.fields[index]

    def _ensure_split(self):
        if self.fields is None:
            self.fields = self.split(self.text)

    def __len__(self):
        self._ensure_split()
        return len(self.fields)

    def __str__(self):
        return self.text

    def __repr__(self):
        return '{}({}, {})'.format(type(self), repr(self.text),
                                   repr(self.split))


def _split_columns(columns, text):
    return [text[begin:end] for begin, end in columns]


def _make_columns(widths):
    offset = 0
    offsets = []
    for width in widths:
        offsets.append(offset)
        if width is Ellipsis:
            offset = None
            break
        offset += width
    ends = offsets[1:] + [offset]
    return list(zip(offsets, ends))


def records(iterable, *, separator=None, widths=None, pattern=None):
    """Generate LazyRecords from iterable of strings.

    Without extra arguments each string is split on whitespace.

    Args:
        iterable: strings
        separator: str or re.Pattern on which input will be split (AWK: FS)
        widths: a list of column widths; may end with ... (Ellipsis)
            which means "remaining characters" (AWK: FIELDWIDTHS)
        pattern: str (a regular expression) or re.Pattern that describes
            the contents of each field (AWK: FPAT)

    Returns:
        Iterable of LazyRecords
    """
    if widths:
        split = partial(_split_columns, _make_columns(widths))
    elif isinstance(separator, str):
        def split(text):
            return text.split(separator)
    elif isinstance(separator, re.Pattern):
        split = separator.split
    elif isinstance(pattern, str):
        split = re.compile(pattern).findall
    elif isinstance(pattern, re.Pattern):
        split = pattern.findall
    else:
        def split(text):
            text.split()
    for text in iterable:
        yield LazyRecord(text, split)
