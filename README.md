# mini-topological-sort

A topological sort that reports the specific cycle when ordering fails.

```python
from mini_topological_sort import topological_sort, CycleError

graph = {
    "install": ["download"],
    "download": ["auth"],
    "auth": [],
}
print(topological_sort(graph))  # ['auth', 'download', 'install']

cyclic = {"a": ["b"], "b": ["c"], "c": ["a"]}
try:
    topological_sort(cyclic)
except CycleError as e:
    print(e.cycle)  # e.g. ['a', 'b', 'c', 'a']
```

## Why

Most topological sort implementations tell you a cycle exists but not
which nodes form it. When you are ordering build steps or service
startups, that difference is between a one-line fix and an hour of
diff-reading. This library walks the remaining edges after Kahn's
algorithm stalls and returns a concrete cycle path on
`CycleError.cycle`.

The trade-off: the successful path is plain Kahn's algorithm with a
FIFO queue, so the ordering is deterministic but not lexicographically
minimal. If you need a specific tie-breaking order, sort the input
graph keys before calling.

## Edges to know about

- A node referenced as a dependency but not present as a key is allowed
  and treated as a node with no further dependencies. `{"a": ["b"]}`
  works and yields `["b", "a"]`.
- Duplicate edges are collapsed silently.
- `CycleError` subclasses `ValueError`, so you can catch the builtin if
  you do not need the cycle path.
- All nodes and dependency names must be strings. The type check is
  explicit and raises `TypeError` early rather than failing deep in the
  traversal.
