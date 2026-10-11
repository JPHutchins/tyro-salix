"""Tests for Python eval-based collections.

These tests verify that tyro can parse collections using Python syntax
(e.g., "[128, 128, 128]", "{'a': 1}") via eval() when the
UsePythonSyntaxForLiteralCollections marker is used.

The eval() approach supports both literal values and non-literal types like
pathlib.Path by making common types available in a secure eval() context.

This is particularly useful for wandb sweeps integration.
"""

from typing import Dict, List, Literal, Optional, Set, Tuple, Union

import pytest
from salix import Struct

import tyro


def test_tuple_python_syntax() -> None:
    """Test that Python literal syntax works for tuples."""

    class Config(Struct, frozen=False):
        dims: Tuple[int, int, int]

    # Normal usage without marker.
    assert tyro.cli(Config, args=["--dims", "1", "2", "3"]) == Config(dims=(1, 2, 3))

    # With UsePythonSyntaxForLiteralCollections marker.
    assert tyro.cli(
        Config,
        args=["--dims", "(1, 2, 3)"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    ) == Config(dims=(1, 2, 3))


def test_tuple_strings() -> None:
    """Test Python syntax for tuples with string elements."""

    class Config(Struct, frozen=False):
        names: Tuple[str, str]

    assert tyro.cli(
        Config,
        args=["--names", "('foo', 'bar')"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    ) == Config(names=("foo", "bar"))


def test_list_python_syntax() -> None:
    """Test Python syntax for lists."""

    class Config(Struct, frozen=False):
        values: List[int]

    # Normal usage without marker.
    assert tyro.cli(Config, args=["--values", "1", "2", "3"]) == Config(
        values=[1, 2, 3]
    )

    # With UsePythonSyntaxForLiteralCollections marker.
    assert tyro.cli(
        Config,
        args=["--values", "[1, 2, 3]"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    ) == Config(values=[1, 2, 3])


def test_dict_python_syntax() -> None:
    """Test Python syntax for dicts."""

    class Config(Struct, frozen=False):
        mapping: Dict[str, int]

    # Normal usage without marker.
    result = tyro.cli(Config, args=["--mapping", "a", "1", "b", "2"])
    assert result == Config(mapping={"a": 1, "b": 2})

    # With UsePythonSyntaxForLiteralCollections marker.
    result = tyro.cli(
        Config,
        args=["--mapping", "{'a': 1, 'b': 2}"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result == Config(mapping={"a": 1, "b": 2})


def test_set_python_syntax() -> None:
    """Test Python syntax for sets."""

    class Config(Struct, frozen=False):
        values: Set[int]

    result = tyro.cli(
        Config,
        args=["--values", "{1, 2, 3}"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result == Config(values={1, 2, 3})


def test_nested_structure() -> None:
    """Test nested structures with Python syntax."""

    class Inner(Struct, frozen=False):
        size: Tuple[int, int]

    class Outer(Struct, frozen=False):
        inner: Inner

    result = tyro.cli(
        Outer,
        args=["--inner.size", "(100, 200)"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result == Outer(inner=Inner(size=(100, 200)))


def test_mixed_types() -> None:
    """Test tuple with mixed numeric types."""

    class Config(Struct, frozen=False):
        mixed: Tuple[int, float, int]

    result = tyro.cli(
        Config,
        args=["--mixed", "(1, 2.5, 3)"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result == Config(mixed=(1, 2.5, 3))


def test_invalid_python_syntax() -> None:
    """Test that invalid Python syntax raises an error."""

    class Config(Struct, frozen=False):
        values: List[int]

    with pytest.raises(SystemExit):
        tyro.cli(
            Config,
            args=["--values", "[1, 2, "],
            config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
        )


def test_type_mismatch() -> None:
    """Test that type mismatches raise an error."""

    class Config(Struct, frozen=False):
        values: Tuple[int, int]

    # Passing a list when expecting a tuple.
    with pytest.raises(SystemExit):
        tyro.cli(
            Config,
            args=["--values", "[1, 2]"],
            config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
        )


def test_helptext_coverage() -> None:
    """Test helptext generation to cover str_from_instance."""
    import sys

    class Config(Struct, frozen=False):
        simple: List[int] = [1, 2, 3]
        nested: List[Tuple[int, str]] = [(1, "a"), (2, "b")]

    # Getting helptext will call str_from_instance for defaults.
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        tyro.cli(Config, config=(tyro.conf.UsePythonSyntaxForLiteralCollections,))


def test_union_with_default() -> None:
    """Test union types with defaults to cover is_instance_fn."""
    import sys

    class Config(Struct, frozen=False):
        value: Union[Tuple[int, ...], int] = 3

    # Getting helptext with a union default exercises is_instance.
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        tyro.cli(Config, config=(tyro.conf.UsePythonSyntaxForLiteralCollections,))


def test_variable_length_tuple() -> None:
    """Test variable-length tuples."""

    class Config(Struct, frozen=False):
        values: Tuple[int, ...]

    result = tyro.cli(
        Config,
        args=["--values", "(1, 2, 3, 4, 5)"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result == Config(values=(1, 2, 3, 4, 5))


def test_nested_union_metavar() -> None:
    """Test metavar generation for nested union types to cover edge cases."""
    import sys
    from typing import Union

    class Config(Struct, frozen=False):
        # This will exercise the metavar generation with Union types.
        values: List[Union[int, str]]

    # Getting helptext will generate metavar for the type.
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        tyro.cli(Config, config=(tyro.conf.UsePythonSyntaxForLiteralCollections,))


def test_nested_literal_metavar() -> None:
    """Test metavar generation for Literal types (which lack __name__)."""
    import sys

    class Config(Struct, frozen=False):
        # Literal types don't have __name__, testing edge case in metavar generation.
        values: List[Literal["a", "b"]]

    # Getting helptext will generate metavar for the type.
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        tyro.cli(Config, config=(tyro.conf.UsePythonSyntaxForLiteralCollections,))


def test_pathlib_fallback() -> None:
    """Test that Path types fall back to normal handling (not literal-eval compatible)."""
    from pathlib import Path

    class Config(Struct, frozen=False):
        paths: List[Path]

    # Path is not compatible with ast.literal_eval, so this should use normal
    # multi-arg parsing even with the marker present.
    result = tyro.cli(
        Config,
        args=["--paths", "foo", "bar"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result == Config(paths=[Path("foo"), Path("bar")])


def test_unparameterized_generic_fallback() -> None:
    """Test that unparameterized generics fall back to other rules."""
    # When a collection type has no type args, the eval rule should return None
    # and let other rules handle it. typing.List without subscript has origin=list
    # but no args, which triggers this early return path.
    from typing import List

    class Config(Struct, frozen=False):
        # Using unparameterized typing.List triggers the early return.
        # It will be handled by other rules as a list with inferred type.
        values: List = None  # type: ignore

    # This should work - the eval rule returns None, other rules handle it.
    result = tyro.cli(
        Config,
        args=[],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.values is None


def test_incompatible_type_fallback() -> None:
    """Test that incompatible types are properly validated and marker is ignored."""
    # When collection contains non-eval-compatible types, the marker is ignored.

    class Inner(Struct, frozen=False):
        value: int

    class Config(Struct, frozen=False):
        # Inner is a struct type (dataclass), so marker is ignored.
        # Tyro falls back to normal handling (requires explicit default).
        items: List[Inner] = []

    # With empty list default, tyro should use it.
    result = tyro.cli(
        Config,
        args=[],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.items == []


def test_literal_type_support() -> None:
    """Test that Literal types work with the marker."""

    class Config(Struct, frozen=False):
        values: List[Literal["a", "b", "c"]]

    # With marker, should accept Python literal syntax.
    result = tyro.cli(
        Config,
        args=["--values", "['a', 'b', 'c']"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.values == ["a", "b", "c"]


def test_literal_int_support() -> None:
    """Test that Literal with int values works."""

    class Config(Struct, frozen=False):
        values: Tuple[Literal[1, 2, 3], Literal[1, 2, 3]]

    result = tyro.cli(
        Config,
        args=["--values", "(1, 2)"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.values == (1, 2)


def test_optional_with_literal() -> None:
    """Test Optional[Literal[...]] works."""

    class Config(Struct, frozen=False):
        value: Optional[List[Literal["x", "y", "z"]]] = None

    result = tyro.cli(
        Config,
        args=[],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.value is None

    result = tyro.cli(
        Config,
        args=["--value", "['x', 'y']"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.value == ["x", "y"]


def test_custom_class_fallback() -> None:
    """Test that custom classes fall back to normal handling."""

    class CustomClass:
        def __init__(self, value: int):
            self.value = value

    class Config(Struct, frozen=False):
        # CustomClass is not a built-in, so marker should be ignored.
        # Tyro falls back to normal handling (treating as struct with default).
        items: List[CustomClass] = []

    # With an empty list default, tyro should use it.
    result = tyro.cli(
        Config,
        args=[],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.items == []


def test_unsupported_builtins_fallback() -> None:
    """Test that unsupported built-in types (frozenset, range, slice) fall back."""

    class Config(Struct, frozen=False):
        # frozenset is a built-in type but not supported by ast.literal_eval().
        # Tyro falls back to normal handling (treating as struct with default).
        values: List[frozenset] = []

    # With an empty list default, tyro should use it.
    result = tyro.cli(
        Config,
        args=[],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.values == []


def test_complex_number_support() -> None:
    """Test that complex numbers work with the marker."""

    class Config(Struct, frozen=False):
        values: List[complex]

    result = tyro.cli(
        Config,
        args=["--values", "[1+2j, 3+4j, 5+0j]"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.values == [1 + 2j, 3 + 4j, 5 + 0j]


def test_literal_metavar_formatting() -> None:
    """Test that Literal types are formatted correctly in metavar."""
    import sys

    class Config(Struct, frozen=False):
        # String literals.
        str_literals: List[Literal["a", "b", "c"]]
        # Int literals.
        int_literals: Tuple[Literal[1, 2, 3], Literal[4, 5, 6]]
        # Nested with Literal.
        nested: List[Tuple[Literal["x", "y"], int]]

    # Getting helptext will show the metavar.
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        tyro.cli(Config, config=(tyro.conf.UsePythonSyntaxForLiteralCollections,))


def test_bytes_support() -> None:
    """Test that bytes work with the marker."""

    class Config(Struct, frozen=False):
        values: List[bytes]

    result = tyro.cli(
        Config,
        args=["--values", "[b'hello', b'world']"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.values == [b"hello", b"world"]


def test_mixed_literal_and_regular_types() -> None:
    """Test mixing Literal types with regular types in collections."""

    class Config(Struct, frozen=False):
        # Tuple with Literal and regular types.
        mixed: Tuple[Literal["a", "b"], int, str]

    result = tyro.cli(
        Config,
        args=["--mixed", "('a', 42, 'hello')"],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.mixed == ("a", 42, "hello")


def test_none_in_tuple() -> None:
    """Test that None works correctly in tuples."""

    class Config(Struct, frozen=False):
        # Tuple with None.
        value: Tuple[int, None]
        # List of tuples with None.
        values: List[Tuple[str, None]]

    result = tyro.cli(
        Config,
        args=[
            "--value",
            "(42, None)",
            "--values",
            "[('a', None), ('b', None)]",
        ],
        config=(tyro.conf.UsePythonSyntaxForLiteralCollections,),
    )
    assert result.value == (42, None)
    assert result.values == [("a", None), ("b", None)]


def test_none_metavar() -> None:
    """Test that None is formatted as 'None' in metavar (not 'NONETYPE')."""
    import sys

    class Config(Struct, frozen=False):
        value: Tuple[int, None]

    # Getting helptext will show the metavar.
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        tyro.cli(Config, config=(tyro.conf.UsePythonSyntaxForLiteralCollections,))
