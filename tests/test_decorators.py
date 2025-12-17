import unittest
from dataclasses import dataclass
from universal_decorator.decorators import (
    to_dataclass_function,
    from_dataclass_function,
    node,
)
from typing import Any
from universal_decorator.metadata import Metadata


class TestNodeDecorator(unittest.TestCase):
    def test_node_decorator_on_function(self):
        @node()
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        metadata: Metadata | None = getattr(add, "__metadata__", None)
        if metadata is not None:
            self.assertIn("a", metadata.inputs)
            self.assertEqual(metadata.inputs["a"].datatype, int)
            self.assertIn("b", metadata.inputs)
            self.assertEqual(metadata.inputs["b"].datatype, int)
            self.assertIn("output", metadata.outputs)
            self.assertEqual(metadata.outputs["output"].datatype, int)
            self.assertEqual(metadata.docstring, "Add two numbers.")
            self.assertEqual(len(metadata.source_code_hash), 64)  # SHA-256 hash length
        else:
            self.fail("Function 'add' does not have __metadata__ attribute.")


class TestToDataclassFunction(unittest.TestCase):
    def setUp(self):
        @to_dataclass_function
        @dataclass
        class Input:
            name: str
            age: int

        self.Input = Input

    def test_to_dataclass_function(self):
        result = self.Input(name="Alice", age=30)
        self.assertIsInstance(result, self.Input.__wrapped__)
        self.assertEqual(result, self.Input.__wrapped__("Alice", 30))


class TestFromDataclassFunction(unittest.TestCase):
    def setUp(self):
        @from_dataclass_function
        @dataclass
        class Output:
            name: str
            age: int

        self.Output = Output

    def test_from_dataclass_function(self):
        data = self.Output.__wrapped__("Alice", 30)

        result = self.Output(data)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, ("Alice", 30))
        self.assertDictEqual(
            self.Output.__annotations__,
            {"input": self.Output.__wrapped__, "return": tuple[Any]},
        )


if __name__ == "__main__":
    unittest.main()
