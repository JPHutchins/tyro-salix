"""Test that OmitArgPrefixes strips parent field name from section headers."""

from __future__ import annotations

from helptext_utils import get_helptext_with_checks
from salix import Struct
from typing_extensions import Annotated

from tyro.conf import OmitArgPrefixes, OmitSubcommandPrefixes, subcommand


class Nested(Struct, frozen=False):
    """nested options"""

    option: str = "value"


class RunConfig(Struct, frozen=False):
    """run tests"""

    num: int = 5
    nested: Nested = Nested()


class CompareConfig(Struct, frozen=False):
    """compare runs"""

    a: str = "x"
    b: str = "y"


def test_omit_arg_prefixes_strips_group_headers():
    """OmitArgPrefixes on a subcommand union field should strip the parent
    field name from section headers in help text."""

    class Config(Struct, frozen=False):
        command: OmitArgPrefixes[
            OmitSubcommandPrefixes[
                Annotated[RunConfig, subcommand("run", prefix_name=False)]
                | Annotated[CompareConfig, subcommand("compare", prefix_name=False)]
            ]
        ] = RunConfig()

    helptext = get_helptext_with_checks(Config, args=["run", "--help"])

    # Section headers should NOT have "command." prefix
    assert "command.nested" not in helptext
    assert "command options" not in helptext

    # But should still have the nested struct's own section header
    assert "nested" in helptext


def test_without_omit_arg_prefixes_keeps_group_headers():
    """Without OmitArgPrefixes, section headers should include the field name."""

    class Config(Struct, frozen=False):
        command: OmitSubcommandPrefixes[
            Annotated[RunConfig, subcommand("run", prefix_name=False)]
            | Annotated[CompareConfig, subcommand("compare", prefix_name=False)]
        ] = RunConfig()

    helptext = get_helptext_with_checks(Config, args=["run", "--help"])

    # Section headers SHOULD have "command" prefix (default behavior)
    assert "command" in helptext
