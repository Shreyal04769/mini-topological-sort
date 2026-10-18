"""Topological sort with cycle reporting.

This module implements Kahn's algorithm for topological sorting of a
 directed acyclic graph. Unlike a naive implementation that merely detects
 the *presence* of a cycle, this one walks the cycle edges to report a
 concrete cycle path, so callers can tell the user exactly which
dependencies form the loop.
"""

from __future__ import annotations


class CycleError(ValueError):
    """Raised when the dependency graph contains a cycle.

    The ``cycle`` attribute holds a list of nodes describing the cycle path.
    For example, ``["a", "b", "c", "a"]`` means ``a -> b -> c -> a``.

    We subclass ValueError so callers who only care that ordering failed
    can catch the builtin; callers who need the path can catch CycleError.
    """

    def __init__(self, message: str, cycle: list[str]) -> None:
        super().__init__(message)
        self.cycle = cycle


def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    """Return a topological ordering of the nodes in *graph*.

    *graph* maps each node to the list of nodes it depends on (i.e., its
    successors / prerequisites). A node must appear in the result before
    any node that lists it as a dependency.

    Duplicate edges are tolerated and treated as a single edge.
    A node listed as a dependency but not present as a key is allowed and
    is treated as a node with no further dependencies.

    Raises CycleError with a ``cycle`` attribute if the graph contains a
    cycle. The cycle is reported as a list of nodes where consecutive
    elements form an edge and the last element equals the first.

    The implementation is Kahn's algorithm (in-degree queue) for the
    successful case. For cycle reporting we then trace one concrete cycle
    among the remaining nodes so the error message is actionable rather
    than a bare "cycle detected".
    """
    if not isinstance(graph, dict):
        raise TypeError(
            f"graph must be a dict, got {type(graph).__name__}"
        )

    # Validate edge list types up front so we fail fast with a clear error
    # instead of a confusing AttributeError deep in the algorithm.
    for node, deps in graph.items():
        if not isinstance(node, str):
            raise TypeError(
                f"graph keys must be str, got {type(node).__name__}"
            )
        if not isinstance(deps, list):
            raise TypeError(
                f"dependencies for {node!r} must be a list, "
                f"got {type(deps).__name__}"
            )
        for dep in deps:
            if not isinstance(dep, str):
                raise TypeError(
                    f"dependencies for {node!r} must all be str, "
                    f"got {type(dep).__name__}"
                )

    # Build the set of all nodes: explicit keys plus any node referenced
    # as a dependency but never declared as a key. We allow the latter so
    # callers can express "x depends on y" without also writing y: [].
    all_nodes: set[str] = set(graph.keys())
    for deps in graph.values():
        all_nodes.update(deps)

    # Adjacency: for each node, the set of nodes that depend on it
    # (reverse edges). We use sets to collapse duplicate edges.
    dependents: dict[str, set[str]] = {node: set() for node in all_nodes}
    indegree: dict[str, int] = {node: 0 for node in all_nodes}

    for node, deps in graph.items():
        seen_for_node: set[str] = set()
        for dep in deps:
            if dep == node:
                raise CycleError(
                    f"cycle detected: {node} -> {node}",
                    [node, node],
                )
            if dep in seen_for_node:
                continue
            seen_for_node.add(dep)
            dependents[dep].add(node)
            indegree[node] += 1

    # Kahn's algorithm: start with all nodes that have no dependencies.
    # Using a list as a FIFO queue gives a stable, deterministic order
    # that respects insertion sequence of the graph keys where possible.
    queue: list[str] = [
        node for node in graph.keys() if indegree[node] == 0
    ]
    # Add referenced-but-undeclared nodes with no dependencies. They go
    # after declared nodes so the output is deterministic.
    for node in all_nodes:
        if node not in graph and indegree[node] == 0:
            queue.append(node)

    result: list[str] = []
    while queue:
        node = queue.pop(0)
        result.append(node)
        for dependent in sorted(dependents[node]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                queue.append(dependent)

    if len(result) == len(all_nodes):
        return result

    # There is a cycle among the nodes not yet emitted. Find one concrete
    # cycle to report so the error is actionable.
    remaining = [n for n in all_nodes if n not in set(result)]
    cycle = _find_cycle(remaining, graph)
    cycle_str = " -> ".join(cycle)
    raise CycleError(
        f"cycle detected: {cycle_str}",
        cycle,
    )


def _find_cycle(
    nodes: list[str], graph: dict[str, list[str]]
) -> list[str]:
    """Find and return one cycle among *nodes* as a closed path list.

    We do a DFS over the subgraph induced by *nodes*. When we encounter a
    node already on the current recursion stack, the slice of the stack
    from that node to the end plus the repeating node is the cycle.

    This is O(V + E) over the remaining subgraph only, which is the
    minimal work needed to report a cycle path.
    """
    remaining_set = set(nodes)
    # For cycle tracing we only care about edges within the remaining set.
    adj: dict[str, list[str]] = {}
    for n in nodes:
        adj[n] = [
            d for d in graph.get(n, [])
            if d in remaining_set
        ]

    stack: list[str] = []
    on_stack: set[str] = set()
    visited: set[str] = set()

    for start in nodes:
        if start in visited:
            continue
        found = _dfs_cycle(start, adj, stack, on_stack, visited)
        if found is not None:
            return found

    # Should be unreachable if we got here from Kahn's leftover check.
    raise CycleError("cycle detected but no cycle found", [])


def _dfs_cycle(
    node: str,
    adj: dict[str, list[str]],
    stack: list[str],
    on_stack: set[str],
    visited: set[str],
) -> list[str] | None:
    """Recursive DFS that returns a cycle path when one is found."""
    if node in on_stack:
        idx = stack.index(node)
        return stack[idx:] + [node]
    if node in visited:
        return None

    stack.append(node)
    on_stack.add(node)
    visited.add(node)

    for neighbor in adj.get(node, []):
        found = _dfs_cycle(neighbor, adj, stack, on_stack, visited)
        if found is not None:
            return found

    stack.pop()
    on_stack.discard(node)
    return None
