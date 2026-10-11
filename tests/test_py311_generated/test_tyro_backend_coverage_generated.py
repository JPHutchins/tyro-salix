"""Tests to improve coverage of _tyro_backend.py."""

from typing import Annotated, List, Literal, Optional, Tuple

import pytest
from salix import Struct

import tyro


def test_positional():
    def main(
        x: int,
        y: int,
        /,
        # Note: it's generally a bad idea to have a mutable object (like a list) as a
        # default value. But it should still work.
        z: List[int] = [1, 2, 3],
    ) -> Tuple[int, int, int]:
        """main.

        Args:
            x: x
            y: y
            z: z

        Returns:
            Tuple[int, int, int]: Output.
        """
        return (x, y, z[0])

    assert tyro.cli(
        main, args="1 2 --z 3".split(" "), config=(tyro.conf.CascadeSubcommandArgs,)
    ) == (1, 2, 3)
    with pytest.raises(SystemExit):
        assert tyro.cli(
            main,
            args="--x 1 --y 2 --z 3".split(" "),
            config=(tyro.conf.CascadeSubcommandArgs,),
        ) == (1, 2, 3)


def test_cascade_misplaced_subcommand() -> None:
    """Test when subcommand appears after other arguments in cascaded mode."""

    class SubcommandA(Struct, frozen=False):
        value: int = 1

    class SubcommandB(Struct, frozen=False):
        value: int = 2

    class Config(Struct, frozen=False):
        x: int
        subcommand: SubcommandA | SubcommandB

    if tyro._experimental_options["backend"] == "tyro":
        assert tyro.cli(
            tyro.conf.CascadeSubcommandArgs[Config],
            args=["--x", "5", "subcommand:subcommand-a"],
        ) == Config(x=5, subcommand=SubcommandA())
    else:
        with pytest.raises(SystemExit):
            tyro.cli(
                tyro.conf.CascadeSubcommandArgs[Config],
                args=["--x", "5", "subcommand:subcommand-a"],
            )


def test_cascade_optional_nargs() -> None:
    """Test nargs='?' handling in cascaded mode."""

    class SubcommandA(Struct, frozen=False):
        required_value: int
        optional_value: Optional[int] = None

    class SubcommandB(Struct, frozen=False):
        value: int = 1

    class Config(Struct, frozen=False):
        subcommand: SubcommandA | SubcommandB

    # Test with the optional value provided.
    result = tyro.cli(
        tyro.conf.CascadeSubcommandArgs[Config],
        args=[
            "subcommand:subcommand-a",
            "--subcommand.required-value",
            "10",
            "--subcommand.optional-value",
            "42",
        ],
    )
    assert isinstance(result.subcommand, SubcommandA)
    assert result.subcommand.required_value == 10
    assert result.subcommand.optional_value == 42

    # Test without the optional value.
    result = tyro.cli(
        tyro.conf.CascadeSubcommandArgs[Config],
        args=["subcommand:subcommand-a", "--subcommand.required-value", "10"],
    )
    assert isinstance(result.subcommand, SubcommandA)
    assert result.subcommand.required_value == 10
    assert result.subcommand.optional_value is None


def test_cascade_positional_values() -> None:
    """Test variadic positional arguments in cascaded mode."""

    class SubcommandA(Struct, frozen=False):
        values: Tuple[int, ...]

    class SubcommandB(Struct, frozen=False):
        value: int = 1

    class Config(Struct, frozen=False):
        subcommand: SubcommandA | SubcommandB

    result = tyro.cli(
        tyro.conf.CascadeSubcommandArgs[Config],
        args=[
            "subcommand:subcommand-a",
            "--subcommand.values",
            "1",
            "2",
            "3",
        ],
    )
    assert isinstance(result.subcommand, SubcommandA)
    assert result.subcommand.values == (1, 2, 3)


def test_cascade_nargs_plus_empty() -> None:
    """Test nargs='+' with values in cascaded mode."""

    class SubcommandA(Struct, frozen=False):
        values: Tuple[int, ...]

    class SubcommandB(Struct, frozen=False):
        value: int = 1

    class Config(Struct, frozen=False):
        subcommand: SubcommandA | SubcommandB

    result = tyro.cli(
        tyro.conf.CascadeSubcommandArgs[Config],
        args=[
            "subcommand:subcommand-a",
            "--subcommand.values",
            "1",
            "2",
        ],
    )
    assert isinstance(result.subcommand, SubcommandA)
    assert result.subcommand.values == (1, 2)


def test_cascade_count_flag_basic() -> None:
    """Test count flags in cascaded mode."""

    class Command(Struct, frozen=False):
        verbose: Annotated[
            tyro.conf.UseCounterAction[int], tyro.conf.arg(aliases=["-v"])
        ] = 0

    assert (
        tyro.cli(
            Command,
            config=(tyro.conf.UseCounterAction, tyro.conf.CascadeSubcommandArgs),
            args=["-vvv"],
        ).verbose
        == 3
    )
    assert (
        tyro.cli(
            Command,
            config=(tyro.conf.UseCounterAction, tyro.conf.CascadeSubcommandArgs),
            args=["-v", "-v", "-v"],
        ).verbose
        == 3
    )


def test_cascade_count_flag() -> None:
    """Test count flags in cascaded mode."""

    class SubcommandA(Struct, frozen=False):
        verbose: tyro.conf.UseCounterAction[int] = 0

    class SubcommandB(Struct, frozen=False):
        value: int = 1

    class Config(Struct, frozen=False):
        subcommand: SubcommandA | SubcommandB

    result = tyro.cli(
        tyro.conf.CascadeSubcommandArgs[Config],
        args=[
            "subcommand:subcommand-a",
            "--subcommand.verbose",
            "--subcommand.verbose",
            "--subcommand.verbose",
        ],
    )
    assert isinstance(result.subcommand, SubcommandA)
    assert result.subcommand.verbose == 3


def test_cascade_flag_with_equals() -> None:
    """Test --flag=value syntax in cascaded mode."""

    class SubcommandA(Struct, frozen=False):
        value: int = 1

    class SubcommandB(Struct, frozen=False):
        value: int = 2

    class Config(Struct, frozen=False):
        subcommand: SubcommandA | SubcommandB

    result = tyro.cli(
        tyro.conf.CascadeSubcommandArgs[Config],
        args=["subcommand:subcommand-a", "--subcommand.value=42"],
    )
    assert isinstance(result.subcommand, SubcommandA)
    assert result.subcommand.value == 42


def test_cascade_unknown_positional() -> None:
    """Test handling of unknown positional arguments in cascaded mode."""

    class SubcommandA(Struct, frozen=False):
        value: int = 1

    class SubcommandB(Struct, frozen=False):
        value: int = 2

    class Config(Struct, frozen=False):
        subcommand: SubcommandA | SubcommandB

    # This should fail because there's an unknown positional argument.
    with pytest.raises(SystemExit):
        tyro.cli(
            tyro.conf.CascadeSubcommandArgs[Config],
            args=["subcommand:subcommand-a", "unknown_positional"],
        )


def test_cascade_default_subcommand() -> None:
    """Test default subcommand handling in cascaded mode."""

    class SubcommandA(Struct, frozen=False):
        value: int = 1

    class SubcommandB(Struct, frozen=False):
        value: int = 2

    class Config(Struct, frozen=False):
        subcommand: SubcommandA | SubcommandB = SubcommandA()

    result = tyro.cli(
        tyro.conf.CascadeSubcommandArgs[Config],
        args=[],
        default=Config(),
    )
    assert isinstance(result.subcommand, SubcommandA)
    assert result.subcommand.value == 1


def test_recursive_mode_default_subcommand() -> None:
    """Test default subcommand in recursive mode."""

    class SubcommandA(Struct, frozen=False):
        value: int = 1

    class SubcommandB(Struct, frozen=False):
        value: int = 2

    class Config(Struct, frozen=False):
        subcommand: SubcommandA | SubcommandB = SubcommandA()

    result = tyro.cli(
        Config,
        args=[],
        default=Config(),
    )
    assert isinstance(result.subcommand, SubcommandA)
    assert result.subcommand.value == 1


def test_recursive_mode_unknown_args() -> None:
    """Test unknown arguments in recursive mode cause an error."""

    class Config(Struct, frozen=False):
        value: int = 1

    # Unknown args should cause an error.
    with pytest.raises(SystemExit):
        tyro.cli(
            Config,
            args=["--value", "42", "--unknown"],
        )


def test_choices_validation() -> None:
    """Test choices validation."""

    class Config(Struct, frozen=False):
        option: Literal["a", "b", "c"]

    result = tyro.cli(Config, args=["--option", "a"])
    assert result.option == "a"

    # This should fail because "d" is not a valid choice.
    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["--option", "d"])


def test_integer_nargs() -> None:
    """Test nargs with integer values."""

    class Config(Struct, frozen=False):
        values: Tuple[int, int, int] = (1, 2, 3)

    result = tyro.cli(Config, args=["--values", "4", "5", "6"], default=Config())
    assert result.values == (4, 5, 6)

    # This should fail because we need exactly 3 values.
    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["--values", "4", "5"], default=Config())


def test_help_flag_display() -> None:
    """Test help flag triggers help display."""

    class Config(Struct, frozen=False):
        value: int = 1

    with pytest.raises(SystemExit) as exc_info:
        tyro.cli(Config, args=["--help"])

    assert exc_info.value.code == 0


def test_cascaded_help_display() -> None:
    """Test help display in cascaded mode."""

    class SubcommandA(Struct, frozen=False):
        value: int = 1

    class SubcommandB(Struct, frozen=False):
        value: int = 2

    class Config(Struct, frozen=False):
        subcommand: SubcommandA | SubcommandB

    with pytest.raises(SystemExit) as exc_info:
        tyro.cli(
            tyro.conf.CascadeSubcommandArgs[Config],
            args=["subcommand:subcommand-a", "--help"],
        )

    assert exc_info.value.code == 0


def test_missing_required_args_error() -> None:
    """Test error when required arguments are missing."""

    class Config(Struct, frozen=False):
        required_value: int

    with pytest.raises(SystemExit):
        tyro.cli(Config, args=[])


def test_boolean_flags() -> None:
    """Test boolean flags with store_true behavior."""

    class Config(Struct, frozen=False):
        verbose: bool = False

    result = tyro.cli(Config, args=["--verbose"], default=Config())
    assert result.verbose is True

    result = tyro.cli(Config, args=[], default=Config())
    assert result.verbose is False


def test_nargs_star() -> None:
    """Test nargs='*' handling."""

    class Config(Struct, frozen=False):
        values: List[int] = []

    result = tyro.cli(Config, args=["--values", "1", "2", "3"], default=Config())
    assert result.values == [1, 2, 3]

    result = tyro.cli(Config, args=[], default=Config())
    assert result.values == []


def test_register_parser_args() -> None:
    """Test registering arguments from parser specification."""

    class Config(Struct, frozen=False):
        value1: int = 1
        value2: str = "test"
        value3: bool = False

    result = tyro.cli(
        Config,
        args=["--value1", "42", "--value2", "hello", "--value3"],
        default=Config(),
    )
    assert result.value1 == 42
    assert result.value2 == "hello"
    assert result.value3 is True


def test_add_help_flags() -> None:
    """Test help flags are registered."""

    class Config(Struct, frozen=False):
        value: int = 1

    # Test both -h and --help.
    with pytest.raises(SystemExit) as exc_info:
        tyro.cli(Config, args=["-h"])
    assert exc_info.value.code == 0

    with pytest.raises(SystemExit) as exc_info:
        tyro.cli(Config, args=["--help"])
    assert exc_info.value.code == 0


def test_validate_required_args() -> None:
    """Test validation of required arguments."""

    class Config(Struct, frozen=False):
        required1: int
        required2: str
        optional: bool = False

    # Should work with all required args.
    result = tyro.cli(
        Config,
        args=["--required1", "42", "--required2", "test"],
    )
    assert result.required1 == 42
    assert result.required2 == "test"
    assert result.optional is False

    # Should fail with missing required args.
    with pytest.raises(SystemExit):
        tyro.cli(Config, args=["--required1", "42"])


def test_short_flag_terminates_nargs_star() -> None:
    """Test that unknown short flags terminate nargs='*' consumption.

    When consuming variable-length arguments (nargs='*'), an unknown short
    flag like -x should terminate consumption, matching argparse behavior.
    """

    class Config(Struct, frozen=False):
        # Variadic string values.
        values: Tuple[str, ...] = ()

    if tyro._experimental_options["backend"] != "tyro":
        pytest.skip("This test is specific to the tyro backend.")

    result, unknown = tyro.cli(
        Config,
        args=["--values", "a", "b", "-x", "c"],
        return_unknown_args=True,
    )
    # -x should NOT be consumed as part of values.
    assert result.values == ("a", "b"), f"Expected ('a', 'b'), got {result.values}"
    assert unknown == ["-x", "c"], f"Expected ['-x', 'c'], got {unknown}"


def test_negative_numbers_in_nargs() -> None:
    """Test that negative numbers are not treated as flags in variadic args."""

    class Config(Struct, frozen=False):
        values: Tuple[int, ...] = ()

    if tyro._experimental_options["backend"] != "tyro":
        pytest.skip("This test is specific to the tyro backend.")

    # Negative integers should be consumed as values, not flags.
    result = tyro.cli(Config, args=["--values", "1", "-2", "3"])
    assert result.values == (1, -2, 3)

    # All negative values.
    result = tyro.cli(Config, args=["--values", "-1", "-2", "-3"])
    assert result.values == (-1, -2, -3)

    # Single negative value.
    result = tyro.cli(Config, args=["--values", "-42"])
    assert result.values == (-42,)


def test_negative_floats_in_nargs() -> None:
    """Test that negative floats are not treated as flags in variadic args."""

    class Config(Struct, frozen=False):
        values: Tuple[float, ...] = ()

    if tyro._experimental_options["backend"] != "tyro":
        pytest.skip("This test is specific to the tyro backend.")

    result = tyro.cli(Config, args=["--values", "1.5", "-3.14", "2.0"])
    assert result.values == (1.5, -3.14, 2.0)

    # Scientific notation with negative exponent.
    result = tyro.cli(Config, args=["--values", "-1e-5"])
    assert result.values == (-1e-5,)


def test_negative_number_with_known_flag() -> None:
    """Test that known flags still terminate nargs even when preceded by negative numbers."""

    class Config(Struct, frozen=False):
        values: Tuple[int, ...] = ()
        flag: int = 0

    if tyro._experimental_options["backend"] != "tyro":
        pytest.skip("This test is specific to the tyro backend.")

    # --flag is a known flag, should terminate consumption.
    result = tyro.cli(Config, args=["--values", "1", "-2", "--flag", "99"])
    assert result.values == (1, -2)
    assert result.flag == 99


def test_negative_numbers_with_unknown_args() -> None:
    """Test negative numbers work alongside unknown flags with return_unknown_args."""

    class Config(Struct, frozen=False):
        values: Tuple[int, ...] = ()

    if tyro._experimental_options["backend"] != "tyro":
        pytest.skip("This test is specific to the tyro backend.")

    result, unknown = tyro.cli(
        Config,
        args=["--values", "1", "-2", "3", "-x", "foo"],
        return_unknown_args=True,
    )
    # -2 should be consumed as a value; -x should not.
    assert result.values == (1, -2, 3)
    assert unknown == ["-x", "foo"]

    # --unknown-flag should also be returned as unknown.
    result, unknown = tyro.cli(
        Config,
        args=["--values", "-5", "--unknown-flag"],
        return_unknown_args=True,
    )
    assert result.values == (-5,)
    assert unknown == ["--unknown-flag"]


def test_bare_dash_in_nargs() -> None:
    """Test that a bare '-' is consumed as a value, not treated as a flag."""

    class Config(Struct, frozen=False):
        values: Tuple[str, ...] = ()

    if tyro._experimental_options["backend"] != "tyro":
        pytest.skip("This test is specific to the tyro backend.")

    result = tyro.cli(Config, args=["--values", "a", "-", "b"])
    assert result.values == ("a", "-", "b")


def test_negative_number_nargs_fixed() -> None:
    """Test that negative numbers work in fixed-length nargs too."""

    class Config(Struct, frozen=False):
        pair: Tuple[int, int] = (0, 0)

    if tyro._experimental_options["backend"] != "tyro":
        pytest.skip("This test is specific to the tyro backend.")

    result = tyro.cli(Config, args=["--pair", "-1", "-2"])
    assert result.pair == (-1, -2)


def test_nested_subcommand_help_prog() -> None:
    """Test that help output for nested subcommands includes full prog path.

    When requesting --help inside a deeply-nested subcommand, the usage line
    should include all intermediate subcommand names, not just the root
    program and the leaf subcommand.
    """
    import io
    import sys

    class Inner1(Struct, frozen=False):
        # Inner field.
        x: int = 1

    class Inner2(Struct, frozen=False):
        # Inner field.
        y: int = 2

    class Middle1(Struct, frozen=False):
        # Nested subcommand.
        inner: Inner1 | Inner2

    class Middle2(Struct, frozen=False):
        # Simple field.
        z: int = 3

    class Outer(Struct, frozen=False):
        # Top-level subcommand.
        cmd: Middle1 | Middle2

    if tyro._experimental_options["backend"] != "tyro":
        pytest.skip("This test is specific to the tyro backend.")

    # Capture help output for the inner-level subcommand.
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        tyro.cli(
            Outer,
            args=["cmd:middle1", "cmd.inner:inner1", "--help"],
            prog="test_prog",
        )
    except SystemExit:
        pass
    sys.stdout = old_stdout
    output = buffer.getvalue()

    # The usage line must include both cmd:middle1 AND cmd.inner:inner1.
    assert "cmd:middle1" in output, (
        f"Expected 'cmd:middle1' in help output, got: {output.splitlines()[0]}"
    )
    assert "cmd.inner:inner1" in output, (
        f"Expected 'cmd.inner:inner1' in help output, got: {output.splitlines()[0]}"
    )


def test_nested_subcommands_cascaded() -> None:
    """Test nested subcommands in cascaded mode."""

    class NestedA(Struct, frozen=False):
        value: int = 1

    class NestedB(Struct, frozen=False):
        value: int = 2

    class SubcommandA(Struct, frozen=False):
        x: int = 10
        nested: NestedA | NestedB = NestedA()

    class Config(Struct, frozen=False):
        subcommand: SubcommandA = SubcommandA()

    result = tyro.cli(
        tyro.conf.CascadeSubcommandArgs[Config],
        args=[],
        default=Config(),
    )
    assert isinstance(result.subcommand, SubcommandA)
    assert isinstance(result.subcommand.nested, NestedA)
