# awking

Make it easier to use Python as an AWK replacement.

## Basic usage

### Extracting groups of lines

```python
from awking import RangeGrouper

lines = '''
text 1
text 2
group start 1
text 3
group end 1
text 4
group start 2
text 5
group end 2
text 6
'''.splitlines()

for group in RangeGrouper('start', 'end', lines):
    print(list(group))
```

This will output:

```text
['group start 1', 'text 3', 'group end 1']
['group start 2', 'text 5', 'group end 2']
```

### Extracting fixed-width fields

```python
from awking import records

ps_aux = '''
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  51120  2796 ?        Ss   Dec22   0:09 /usr/lib/systemd/systemd --system --deserialize 22
root         2  0.0  0.0      0     0 ?        S    Dec22   0:00 [kthreadd]
root         3  0.0  0.0      0     0 ?        S    Dec22   0:04 [ksoftirqd/0]
root         5  0.0  0.0      0     0 ?        S<   Dec22   0:00 [kworker/0:0H]
root         7  0.0  0.0      0     0 ?        S    Dec22   0:15 [migration/0]
root         8  0.0  0.0      0     0 ?        S    Dec22   0:00 [rcu_bh]
root         9  0.0  0.0      0     0 ?        S    Dec22   2:47 [rcu_sched]
saml      3015  0.0  0.0 117756   596 pts/2    Ss   Dec22   0:00 bash
saml      3093  0.9  4.1 1539436 330796 ?      Sl   Dec22  70:16 /usr/lib64/thunderbird/thunderbird
saml      3873  0.0  0.1 1482432 8628 ?        Sl   Dec22   0:02 gvim -f
root      5675  0.0  0.0 124096   412 ?        Ss   Dec22   0:02 /usr/sbin/crond -n
root      5777  0.0  0.0  51132  1068 ?        Ss   Dec22   0:08 /usr/sbin/wpa_supplicant -u -f /var/log/wpa_supplica
saml      5987  0.7  1.5 1237740 119876 ?      Sl   Dec26  14:05 /opt/google/chrome/chrome --type=renderer --lang=en-
root      6115  0.0  0.0      0     0 ?        S    Dec27   0:06 [kworker/0:2]
'''

for user, _, command in records(ps_aux.splitlines(), widths=[7, 58, ...]):
    print(user, command)
```

This will output:

```text
USER    COMMAND
root    /usr/lib/systemd/systemd --system --deserialize 22
root    [kthreadd]
root    [ksoftirqd/0]
root    [kworker/0:0H]
root    [migration/0]
root    [rcu_bh]
root    [rcu_sched]
saml    bash
saml    /usr/lib64/thunderbird/thunderbird
saml    gvim -f
root    /usr/sbin/crond -n
root    /usr/sbin/wpa_supplicant -u -f /var/log/wpa_supplica
saml    /opt/google/chrome/chrome --type=renderer --lang=en-
root    [kworker/0:2]
```

## The problem

Did you ever have to scan a log file for XMLs? How hard was it for you to
extract a set of multi-line XMLs into separate files?

You can use `re.findall` or `re.finditer` but you need to read the entire log
file into a string first. You can also use an AWK script like this one:

```awk
#!/usr/bin/awk -f

/^Payload: <([-_a-zA-Z0-9]+:)?Request/ {
    ofname = "request_" (++index) ".xml"
    sub(/^Payload: /, "")
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

### Python equivalent using `awking`

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

## Caveats

The grouping algorithm reads the input iterable lazily. You can still run out
of memory if you keep references to previous groups without consuming them.
