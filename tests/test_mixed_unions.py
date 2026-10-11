"""Tests for unsupported union types.

Unions like `int | str` or `SomeDataclassA | SomeDataclassB` are OK (note that the latter
will produce a pair of subcommands); when we write things like `int | SomeDataclassA`
handling gets more complicated but should still be supported!
"""

from typing import Any, Dict, List, Tuple, Union

import pytest
from helptext_utils import get_helptext_with_checks
from salix import Struct

import tyro


def test_subparser_strip_non_nested() -> None:
    class DefaultHTTPServer(Struct, frozen=False):
        y: int

    class DefaultSMTPServer(Struct, frozen=False):
        z: int

    class DefaultSubparser(Struct, frozen=False):
        x: int
        # We add [int, str] to the annotation here... this should be ignored.
        bc: Union[int, str, DefaultHTTPServer, DefaultSMTPServer] = DefaultHTTPServer(5)

    assert (
        tyro.cli(
            DefaultSubparser, args=["--x", "1", "bc:default-http-server", "--bc.y", "5"]
        )
        == tyro.cli(DefaultSubparser, args=["--x", "1"])
        == DefaultSubparser(x=1, bc=DefaultHTTPServer(y=5))
    )
    assert tyro.cli(
        DefaultSubparser, args=["--x", "1", "bc:default-smtp-server", "--bc.z", "3"]
    ) == DefaultSubparser(x=1, bc=DefaultSMTPServer(z=3))
    assert (
        tyro.cli(
            DefaultSubparser, args=["--x", "1", "bc:default-http-server", "--bc.y", "8"]
        )
        == tyro.cli(
            DefaultSubparser,
            args=[],
            default=DefaultSubparser(x=1, bc=DefaultHTTPServer(y=8)),
        )
        == DefaultSubparser(x=1, bc=DefaultHTTPServer(y=8))
    )

    with pytest.raises(SystemExit):
        tyro.cli(DefaultSubparser, args=["--x", "1", "b", "--bc.z", "3"])
    with pytest.raises(SystemExit):
        tyro.cli(DefaultSubparser, args=["--x", "1", "c", "--bc.y", "3"])


def test_subparser_strip_nested() -> None:
    class DefaultHTTPServer(Struct, frozen=False):
        y: int

    class DefaultSMTPServer(Struct, frozen=False):
        z: int

    class DefaultSubparser(Struct, frozen=False):
        x: int
        # We add [int, str] to the annotation here... this should be ignored.
        bc: Union[int, str, DefaultHTTPServer, DefaultSMTPServer] = 5

    assert (
        tyro.cli(DefaultSubparser, args=["--x", "1", "bc:int", "5"])
        == tyro.cli(DefaultSubparser, args=["--x", "1"])
        == DefaultSubparser(x=1, bc=5)
    )
    assert tyro.cli(
        DefaultSubparser, args=["--x", "1", "bc:str", "five"]
    ) == DefaultSubparser(x=1, bc="five")


def test_with_fancy_types() -> None:
    class Args(Struct, frozen=False):
        y: int

    def main(x: Union[Tuple[int, ...], List[str], Args, Dict[str, int]]) -> Any:
        return x

    assert tyro.cli(main, args="x:tuple-int-ellipsis 1 2 3".split(" ")) == (1, 2, 3)
    assert tyro.cli(main, args="x:list-str 1 2 3".split(" ")) == ["1", "2", "3"]
    assert tyro.cli(main, args="x:args --x.y 5".split(" ")) == Args(5)
    assert tyro.cli(main, args="x:dict-str-int 1 2 3 4".split(" ")) == {"1": 2, "3": 4}


def test_disallow_none_subcommand() -> None:
    class SubcommandA(Struct, frozen=False):
        value: int

    class Config(Struct, frozen=False):
        subcommand: tyro.conf.DisallowNone[Union[SubcommandA, None]] = None

    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["subcommand:none"])

    # Verify helptext doesn't show none option
    helptext = get_helptext_with_checks(Config)
    assert "subcommand:subcommand-a" in helptext
    assert "subcommand:none" not in helptext


def test_disallow_none_subcommand_backwards_compatibility() -> None:
    class SubcommandA(Struct, frozen=False):
        value: int

    class Config(Struct, frozen=False):
        subcommand: tyro.conf.DisallowNone[Union[SubcommandA, None]] = None

    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["subcommand:None"])


def test_disallow_none_multiple_options() -> None:
    class SubcommandA(Struct, frozen=False):
        a: int

    class SubcommandB(Struct, frozen=False):
        b: str

    class Config(Struct, frozen=False):
        subcommand: tyro.conf.DisallowNone[Union[SubcommandA, SubcommandB, None]] = None

    # Should work with valid subcommands
    result_a = tyro.cli(
        Config, args=["subcommand:subcommand-a", "--subcommand.a", "42"]
    )
    assert isinstance(result_a.subcommand, SubcommandA)
    assert result_a.subcommand.a == 42

    result_b = tyro.cli(
        Config, args=["subcommand:subcommand-b", "--subcommand.b", "hello"]
    )
    assert isinstance(result_b.subcommand, SubcommandB)
    assert result_b.subcommand.b == "hello"

    # Should reject none
    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["subcommand:none"])

    # Should default to None when no args provided
    result_default = tyro.cli(Config, args=[])
    assert result_default.subcommand is None

    # Verify helptext doesn't show none option
    helptext = get_helptext_with_checks(Config)
    assert "subcommand:subcommand-a" in helptext
    assert "subcommand:subcommand-b" in helptext
    assert "subcommand:none" not in helptext


def test_disallow_none_multiple_fields() -> None:
    class SubcommandA(Struct, frozen=False):
        value: int

    class SubcommandB(Struct, frozen=False):
        value: str

    class Config(Struct, frozen=False):
        first: tyro.conf.DisallowNone[Union[SubcommandA, None]] = None
        second: tyro.conf.DisallowNone[Union[SubcommandB, None]] = None

    # Should work with valid subcommands
    result = tyro.cli(
        Config,
        args=[
            "first:subcommand-a",
            "--first.value",
            "42",
            "second:subcommand-b",
            "--second.value",
            "hello",
        ],
    )
    assert isinstance(result.first, SubcommandA)
    assert result.first.value == 42
    assert isinstance(result.second, SubcommandB)
    assert result.second.value == "hello"

    # Should reject none for either field
    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["first:none"])

    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["second:none"])


def test_disallow_none_nested_subcommands() -> None:
    class InnerA(Struct, frozen=False):
        value: int

    class InnerB(Struct, frozen=False):
        inner: tyro.conf.DisallowNone[Union[InnerA, None]] = None

    class Config(Struct, frozen=False):
        outer: tyro.conf.DisallowNone[Union[InnerB, None]] = None

    # Should work with valid nested subcommands
    result = tyro.cli(
        Config,
        args=["outer:inner-b", "outer.inner:inner-a", "--outer.inner.value", "42"],
    )
    assert isinstance(result.outer, InnerB)
    assert isinstance(result.outer.inner, InnerA)
    assert result.outer.inner.value == 42

    # Should reject none at outer level
    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["outer:none"])

    # Should reject none at inner level
    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["outer:inner-b", "outer.inner:none"])


def test_normal_subcommand_helptext_comparison() -> None:
    class SubcommandA(Struct, frozen=False):
        value: int

    class ConfigWithoutDisallowNone(Struct, frozen=False):
        subcommand: Union[SubcommandA, None] = None

    class ConfigWithDisallowNone(Struct, frozen=False):
        subcommand: tyro.conf.DisallowNone[Union[SubcommandA, None]] = None

    normal_helptext = get_helptext_with_checks(ConfigWithoutDisallowNone)
    disallow_helptext = get_helptext_with_checks(ConfigWithDisallowNone)

    # Normal config should show none option
    assert "subcommand:none" in normal_helptext
    assert "subcommand:subcommand-a" in normal_helptext

    # DisallowNone config should NOT show none option
    assert "subcommand:none" not in disallow_helptext
    assert "subcommand:subcommand-a" in disallow_helptext


def test_disallow_none_mixed_primitive_union() -> None:
    class SubcommandA(Struct, frozen=False):
        value: int

    class Config(Struct, frozen=False):
        # This creates a mixed union where some types create subcommands (SubcommandA)
        # and others don't (str), but None is disallowed
        field: tyro.conf.DisallowNone[Union[SubcommandA, str, None]] = None

    # Should work with struct subcommand
    result_struct = tyro.cli(Config, args=["field:subcommand-a", "--field.value", "42"])
    assert isinstance(result_struct.field, SubcommandA)
    assert result_struct.field.value == 42

    # Should work with primitive value
    result_str = tyro.cli(Config, args=["field:str", "hello"])
    assert result_str.field == "hello"

    # Should reject none
    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["field:none"])

    # Should default to None when no args provided
    result_default = tyro.cli(Config, args=[])
    assert result_default.field is None

    # Check helptext doesn't show none
    helptext = get_helptext_with_checks(Config)
    assert "field:subcommand-a" in helptext
    assert "field:str" in helptext
