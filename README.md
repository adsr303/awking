# awking
Make it easier to use Python as an AWK replacement.

## The problem

Did you ever have to scan a log file for XMLs? How hard was it for you to
extract a set of multi-line XMLs into separate files?

You can use `re.findall` or `re.finditer` but you need to read the entire log
file into a string first. You can also use an AWK script like this one:

```awk
#!/usr/bin/awk -f

/^Payload: <([-_a-zA-Z0-9]+:)?Request/ {
    ofname = "request_" (++index) ".xml"
    gsub(/^Payload: /, "")
}

/<([-_a-zA-Z0-9]+:)?Request/, /<\/([-_a-zA-Z0-9]+:)?Request/ {
    print > ofname
}

/<\/([-_a-zA-Z0-9]+:)?Request/ {
    if (ofname) {
        close(ofname)
        ofname = ""
    }
}
```

This works, and quite well. (Despite this being a Python module I encourage you
to learn AWK if you don't already know it.)

But what if you want to build this kind of stuff into your Python application?
What if your input is not lines in a file but a different type of objects?

## Basic usage

The `RangeGrouper` class groups elements from the input iterable based on
predicates for the start and end element. This is a bit like Perl's range
operator or AWK's range pattern, except that your ranges get grouped into
`START..END` iterables.

An equivalent of the above AWK script might look like this:

```python
from awking import RangeGrouper
import re
import sys

g = RangeGrouper(r'^Payload: <([-_a-zA-Z0-9]+:)?Request',
                 r'</([-_a-zA-Z0-9]+:)?Request', sys.stdin)
for index, request in enumerate(g, 1):
    with open(f'request_{index}.xml', 'w') as f:
        for line in request:
            line = re.sub(r'^Payload: ', '', line)  # Not optimal
            print(line, file=f, end='')
```

The predicates may be regular expressions, either as `re.compile()` objects or
strings; or they may be any callables that accept a single argument and return
a true/false value.
