import unittest

from mini_topological_sort import topological_sort, CycleError


class TestTopologicalSort(unittest.TestCase):

    def test_empty_graph(self):
        self.assertEqual(topological_sort({}), [])

    def test_single_node_no_deps(self):
        self.assertEqual(topological_sort({"a": []}), ["a"])

    def test_simple_chain(self):
        graph = {"a": ["b"], "b": ["c"], "c": []}
        result = topological_sort(graph)
        self.assertEqual(result, ["c", "b", "a"])

    def test_diamond(self):
        graph = {
            "d": ["b", "c"],
            "b": ["a"],
            "c": ["a"],
            "a": [],
        }
        result = topological_sort(graph)
        self.assertEqual(result, ["a", "b", "c", "d"])

    def test_independent_nodes_order(self):
        graph = {"x": [], "y": [], "z": []}
        self.assertEqual(topological_sort(graph), ["x", "y", "z"])

    def test_referenced_but_undeclared_node(self):
        graph = {"a": ["b"]}
        result = topological_sort(graph)
        self.assertEqual(result, ["b", "a"])

    def test_duplicate_edges_collapsed(self):
        graph = {"a": ["b", "b"], "b": []}
        result = topological_sort(graph)
        self.assertEqual(result, ["b", "a"])

    def test_self_loop_reports_cycle(self):
        graph = {"a": ["a"]}
        with self.assertRaises(CycleError) as ctx:
            topological_sort(graph)
        self.assertEqual(ctx.exception.cycle, ["a", "a"])

    def test_two_node_cycle(self):
        graph = {"a": ["b"], "b": ["a"]}
        with self.assertRaises(CycleError) as ctx:
            topological_sort(graph)
        cycle = ctx.exception.cycle
        self.assertEqual(len(cycle), 3)
        self.assertEqual(cycle[0], cycle[-1])
        self.assertIn("a", cycle)
        self.assertIn("b", cycle)

    def test_three_node_cycle(self):
        graph = {
            "a": ["b"],
            "b": ["c"],
            "c": ["a"],
        }
        with self.assertRaises(CycleError) as ctx:
            topological_sort(graph)
        cycle = ctx.exception.cycle
        self.assertEqual(cycle[0], cycle[-1])
        # The cycle must contain all three nodes.
        self.assertEqual(set(cycle[:-1]), {"a", "b", "c"})

    def test_cycle_with_extra_non_cycle_nodes(self):
        graph = {
            "x": ["y"],
            "y": [],
            "a": ["b"],
            "b": ["c"],
            "c": ["a"],
        }
        with self.assertRaises(CycleError) as ctx:
            topological_sort(graph)
        cycle = ctx.exception.cycle
        self.assertEqual(cycle[0], cycle[-1])
        self.assertEqual(set(cycle[:-1]), {"a", "b", "c"})
        # x and y must not appear in the reported cycle.
        self.assertNotIn("x", cycle)
        self.assertNotIn("y", cycle)

    def test_cycle_error_is_value_error(self):
        graph = {"a": ["b"], "b": ["a"]}
        with self.assertRaises(ValueError):
            topological_sort(graph)

    def test_type_error_on_non_dict(self):
        with self.assertRaises(TypeError):
            topological_sort([("a", ["b"])])  # type: ignore[arg-type]

    def test_type_error_on_non_list_deps(self):
        with self.assertRaises(TypeError):
            topological_sort({"a": "b"})  # type: ignore[dict-item]

    def test_type_error_on_non_str_node(self):
        with self.assertRaises(TypeError):
            topological_sort({1: []})  # type: ignore[dict-item]

    def test_type_error_on_non_str_dep(self):
        with self.assertRaises(TypeError):
            topological_sort({"a": [1]})  # type: ignore[list-item]


if __name__ == "__main__":
    unittest.main()
