import contextlib
import io
import sys
from typing import (
    Annotated,
    Any,
    Final,
    Generic,
    List,
    Literal,
    NewType,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import pytest
from helptext_utils import get_helptext_with_checks
from salix import Struct

import tyro


def test_nested() -> None:
    class B(Struct, frozen=False):
        y: int

    class Nested(Struct, frozen=False):
        x: int
        b: B
        """Helptext for b"""

    assert tyro.cli(Nested, args=["--x", "1", "--b.y", "3"]) == Nested(x=1, b=B(y=3))
    with pytest.raises(SystemExit):
        tyro.cli(Nested, args=["--x", "1"])

    def main(x: Nested):
        return x

    print(get_helptext_with_checks(main))
    assert "Helptext for b" in get_helptext_with_checks(main)


def test_nested_annotated() -> None:
    class B(Struct, frozen=False):
        y: int

    class Nested(Struct, frozen=False):
        x: int
        b: Annotated[B, "this should be ignored"]

    assert tyro.cli(Nested, args=["--x", "1", "--b.y", "3"]) == Nested(x=1, b=B(y=3))
    with pytest.raises(SystemExit):
        tyro.cli(Nested, args=["--x", "1"])


def test_nested_final() -> None:
    class B(Struct, frozen=False):
        y: int

    class Nested(Struct, frozen=False):
        x: int
        b: Final[B]  # type: ignore

    assert tyro.cli(Nested, args=["--x", "1", "--b.y", "3"]) == Nested(x=1, b=B(y=3))
    with pytest.raises(SystemExit):
        tyro.cli(Nested, args=["--x", "1"])


def test_nested_accidental_underscores() -> None:
    class B(Struct, frozen=False):
        arg_name: str

    class Nested(Struct, frozen=False):
        x: int
        child_struct: B

    assert (
        tyro.cli(Nested, args=["--x", "1", "--child-struct.arg-name", "three_five"])
        == tyro.cli(Nested, args=["--x", "1", "--child_struct.arg_name", "three_five"])
        == tyro.cli(Nested, args=["--x", "1", "--child_struct.arg-name", "three_five"])
        == tyro.cli(Nested, args=["--x", "1", "--child_struct.arg_name=three_five"])
        == Nested(x=1, child_struct=B(arg_name="three_five"))
    )
    with pytest.raises(SystemExit):
        tyro.cli(Nested, args=["--x", "1"])


def test_nested_default() -> None:
    class B(Struct, frozen=False):
        y: int = 1

    class Nested(Struct, frozen=False):
        x: int = 2
        b: B = B()

    assert tyro.cli(Nested, args=[], default=Nested(x=1, b=B(y=2))) == Nested(
        x=1, b=B(y=2)
    )


def test_nested_default_alternate() -> None:
    class B(Struct, frozen=False):
        y: int = 3

    class Nested(Struct, frozen=False):
        x: int
        b: B

    assert (
        Nested(x=1, b=B(y=3))
        == tyro.cli(Nested, args=["--x", "1", "--b.y", "3"])
        == tyro.cli(Nested, args=[], default=Nested(x=1, b=B(y=3)))
    )
    assert tyro.cli(Nested, args=["--x", "1"]) == Nested(x=1, b=B(y=3))


def test_default_nested() -> None:
    class B(Struct, frozen=False):
        y: int = 3

    class Nested(Struct, frozen=False):
        x: int
        b: B = B(y=5)

    assert tyro.cli(Nested, args=["--x", "1", "--b.y", "3"]) == Nested(x=1, b=B(y=3))
    assert tyro.cli(Nested, args=["--x", "1"]) == Nested(x=1, b=B(y=5))


def test_double_default_nested() -> None:
    class Child(Struct):
        y: int

    class Parent(Struct, frozen=False):
        c: Child

    class Grandparent(Struct):
        x: int
        b: Parent = Parent(Child(y=5))

    assert tyro.cli(Grandparent, args=["--x", "1", "--b.c.y", "3"]) == Grandparent(
        x=1, b=Parent(Child(y=3))
    )
    assert tyro.cli(Grandparent, args=["--x", "1"]) == Grandparent(
        x=1, b=Parent(Child(y=5))
    )


def test_default_factory_nested() -> None:
    class B(Struct, frozen=False):
        y: int = 3

    class Nested(Struct, frozen=False):
        x: int
        b: B = B(y=5)

    assert tyro.cli(Nested, args=["--x", "1", "--b.y", "3"]) == Nested(x=1, b=B(y=3))
    assert tyro.cli(Nested, args=["--x", "1"]) == Nested(x=1, b=B(y=5))


def test_optional_nested() -> None:
    class OptionalNestedChild(Struct, frozen=False):
        y: int
        z: int

    class OptionalNested(Struct, frozen=False):
        x: int
        b: Optional[OptionalNestedChild] = None

    assert tyro.cli(OptionalNested, args=["--x", "1"]) == OptionalNested(x=1, b=None)
    with pytest.raises(SystemExit):
        tyro.cli(
            OptionalNested, args=["--x", "1", "b:optional-nested-child", "--b.y", "3"]
        )
    with pytest.raises(SystemExit):
        tyro.cli(
            OptionalNested, args=["--x", "1", "b:optional-nested-child", "--b.z", "3"]
        )

    assert tyro.cli(
        OptionalNested,
        args=["--x", "1", "b:optional-nested-child", "--b.y", "2", "--b.z", "3"],
    ) == OptionalNested(x=1, b=OptionalNestedChild(y=2, z=3))


def test_optional_nested_newtype() -> None:
    class OptionalNestedChild(Struct, frozen=False):
        y: int
        z: int

    SpecialOptionalNestedChild = NewType(
        "SpecialOptionalNestedChild", OptionalNestedChild
    )

    class OptionalNested(Struct, frozen=False):
        x: int
        b: Optional[SpecialOptionalNestedChild] = None

    assert tyro.cli(OptionalNested, args=["--x", "1"]) == OptionalNested(x=1, b=None)
    with pytest.raises(SystemExit):
        tyro.cli(
            OptionalNested,
            args=["--x", "1", "b:special-optional-nested-child", "--b.y", "3"],
        )
    with pytest.raises(SystemExit):
        tyro.cli(
            OptionalNested,
            args=["--x", "1", "b:special-optional-nested-child", "--b.z", "3"],
        )

    assert tyro.cli(
        OptionalNested,
        args=[
            "--x",
            "1",
            "b:special-optional-nested-child",
            "--b.y",
            "2",
            "--b.z",
            "3",
        ],
    ) == OptionalNested(
        x=1, b=SpecialOptionalNestedChild(OptionalNestedChild(y=2, z=3))
    )


def test_optional_nested_multiple() -> None:
    """Adapted from: https://github.com/brentyi/tyro/issues/60"""

    class OutputHeadSettings(Struct):
        number_of_outputs: int = 1

    class OptimizerSettings(Struct):
        name: str = "adam"

    class ModelSettings(Struct):
        output_head_settings: Optional[OutputHeadSettings] = None
        optimizer_settings: Optional[OptimizerSettings] = None

    assert tyro.cli(
        ModelSettings,
        args="output-head-settings:none optimizer-settings:none".split(" "),
    ) == ModelSettings(None, None)

    # With the argparse backend, order cannot be flipped.
    # With the tyro backend, flexible ordering is supported.
    if tyro._experimental_options["backend"] == "argparse":
        with pytest.raises(SystemExit):
            tyro.cli(
                ModelSettings,
                args="optimizer-settings:none output-head-settings:none".split(" "),
            )
    else:
        assert tyro.cli(
            ModelSettings,
            args="optimizer-settings:none output-head-settings:none".split(" "),
        ) == ModelSettings(None, None)

    assert tyro.cli(
        ModelSettings,
        args="output-head-settings:output-head-settings optimizer-settings:none".split(
            " "
        ),
    ) == ModelSettings(OutputHeadSettings(1), None)

    assert tyro.cli(
        ModelSettings,
        args=(
            "output-head-settings:output-head-settings"
            " --output-head-settings.number-of-outputs 5 optimizer-settings:none".split(
                " "
            )
        ),
    ) == ModelSettings(OutputHeadSettings(5), None)
    if tyro._experimental_options["backend"] == "tyro":
        assert tyro.cli(
            ModelSettings,
            args=(
                "output-head-settings:output-head-settings"
                " --output-head-settings.number-of-outputs 5 optimizer-settings:None".split(
                    " "
                )
            ),
        ) == ModelSettings(OutputHeadSettings(5), None)

    assert tyro.cli(
        tyro.conf.OmitSubcommandPrefixes[
            tyro.conf.CascadeSubcommandArgs[ModelSettings]
        ],
        args=("output-head-settings none --number-of-outputs 5".split(" ")),
    ) == ModelSettings(OutputHeadSettings(5), None)

    if tyro._experimental_options["backend"] == "tyro":
        assert tyro.cli(
            tyro.conf.OmitSubcommandPrefixes[
                tyro.conf.CascadeSubcommandArgs[ModelSettings]
            ],
            args=("output-head-settings None --number-of-outputs 5".split(" ")),
        ) == ModelSettings(OutputHeadSettings(5), None)

    assert tyro.cli(
        tyro.conf.OmitSubcommandPrefixes[
            tyro.conf.CascadeSubcommandArgs[ModelSettings]
        ],
        args=(
            "output-head-settings"
            " optimizer-settings --name sgd --number-of-outputs 5".split(" ")
        ),
    ) == ModelSettings(OutputHeadSettings(5), OptimizerSettings("sgd"))


def test_subparser() -> None:
    class HTTPServer(Struct, frozen=False):
        y: int

    class SMTPServer(Struct, frozen=False):
        z: int

    class Subparser(Struct, frozen=False):
        x: int
        bc: HTTPServer | SMTPServer

    assert tyro.cli(
        Subparser, args=["--x", "1", "bc:http-server", "--bc.y", "3"]
    ) == Subparser(x=1, bc=HTTPServer(y=3))
    assert tyro.cli(
        Subparser, args=["--x", "1", "bc:smtp-server", "--bc.z", "3"]
    ) == Subparser(x=1, bc=SMTPServer(z=3))

    with pytest.raises(SystemExit):
        # Missing subcommand.
        tyro.cli(Subparser, args=["--x", "1"])
    with pytest.raises(SystemExit):
        # Wrong field.
        tyro.cli(Subparser, args=["--x", "1", "bc:http-server", "--bc.z", "3"])
    with pytest.raises(SystemExit):
        # Wrong field.
        tyro.cli(Subparser, args=["--x", "1", "bc:smtp-server", "--bc.y", "3"])


def test_subparser_newtype() -> None:
    class HTTPServer(Struct, frozen=False):
        y: int

    class SMTPServer(Struct, frozen=False):
        z: int

    HTTPServer1 = NewType("HTTPServer1", HTTPServer)
    HTTPServer2 = NewType("HTTPServer2", HTTPServer)

    class Subparser(Struct, frozen=False):
        x: int
        bc: HTTPServer1 | HTTPServer2 | SMTPServer

    assert tyro.cli(
        Subparser, args=["--x", "1", "bc:http-server1", "--bc.y", "3"]
    ) == Subparser(x=1, bc=HTTPServer1(HTTPServer(y=3)))
    assert tyro.cli(
        Subparser, args=["--x", "1", "bc:http-server2", "--bc.y", "3"]
    ) == Subparser(x=1, bc=HTTPServer2(HTTPServer(y=3)))
    assert tyro.cli(
        Subparser, args=["--x", "1", "bc:smtp-server", "--bc.z", "3"]
    ) == Subparser(x=1, bc=SMTPServer(z=3))

    with pytest.raises(SystemExit):
        # Missing subcommand.
        tyro.cli(Subparser, args=["--x", "1"])
    with pytest.raises(SystemExit):
        # Wrong field.
        tyro.cli(Subparser, args=["--x", "1", "bc:http-server1", "--bc.z", "3"])
    with pytest.raises(SystemExit):
        # Wrong field.
        tyro.cli(Subparser, args=["--x", "1", "bc:smtp-server", "--bc.y", "3"])


def test_subparser_root() -> None:
    class HTTPServer(Struct, frozen=False):
        y: int

    class SMTPServer(Struct, frozen=False):
        z: int

    class Subparser(Struct, frozen=False):
        x: int
        bc: HTTPServer | SMTPServer

    assert tyro.cli(
        HTTPServer | SMTPServer,
        args=["http-server", "--y", "3"],  # type: ignore
    ) == HTTPServer(y=3)


def test_subparser_with_default() -> None:
    class DefaultHTTPServer(Struct, frozen=False):
        y: int

    class DefaultSMTPServer(Struct, frozen=False):
        z: int

    class DefaultSubparser(Struct, frozen=False):
        x: int
        bc: DefaultHTTPServer | DefaultSMTPServer = DefaultHTTPServer(5)

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


def test_subparser_with_default_and_newtype() -> None:
    class DefaultHTTPServer_(Struct, frozen=False):
        y: int

    DefaultHTTPServer__ = NewType("DefaultHTTPServer__", DefaultHTTPServer_)
    DefaultHTTPServer = NewType("DefaultHTTPServer", DefaultHTTPServer__)  # type: ignore
    # ^nesting NewType is not technically allowed and pyright will complain,
    # but we should try to be robust to it anyways.

    def make_http_server(y: int) -> DefaultHTTPServer:
        return DefaultHTTPServer(DefaultHTTPServer__(DefaultHTTPServer_(y)))

    class DefaultSMTPServer(Struct, frozen=False):
        z: int

    class DefaultSubparser(Struct, frozen=False):
        x: int
        bc: DefaultHTTPServer | DefaultSMTPServer = make_http_server(5)

    assert (
        tyro.cli(
            DefaultSubparser, args=["--x", "1", "bc:default-http-server", "--bc.y", "5"]
        )
        == tyro.cli(DefaultSubparser, args=["--x", "1"])
        == DefaultSubparser(x=1, bc=make_http_server(y=5))
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
            default=DefaultSubparser(x=1, bc=make_http_server(y=8)),
        )
        == DefaultSubparser(x=1, bc=make_http_server(y=8))
    )

    with pytest.raises(SystemExit):
        tyro.cli(DefaultSubparser, args=["--x", "1", "b", "--bc.z", "3"])
    with pytest.raises(SystemExit):
        tyro.cli(DefaultSubparser, args=["--x", "1", "c", "--bc.y", "3"])


def test_subparser_with_default_alternate() -> None:
    class DefaultInstanceHTTPServer(Struct, frozen=False):
        y: int = 0

    class DefaultInstanceSMTPServer(Struct, frozen=False):
        z: int = 0

    class DefaultInstanceSubparser(Struct, frozen=False):
        x: int
        bc: DefaultInstanceHTTPServer | DefaultInstanceSMTPServer

    assert (
        tyro.cli(
            DefaultInstanceSubparser,
            args=["--x", "1", "bc:default-instance-http-server", "--bc.y", "5"],
        )
        == tyro.cli(
            DefaultInstanceSubparser,
            args=[],
            default=DefaultInstanceSubparser(x=1, bc=DefaultInstanceHTTPServer(y=5)),
        )
        == tyro.cli(
            DefaultInstanceSubparser,
            args=["bc:default-instance-http-server"],
            default=DefaultInstanceSubparser(x=1, bc=DefaultInstanceHTTPServer(y=5)),
        )
        == DefaultInstanceSubparser(x=1, bc=DefaultInstanceHTTPServer(y=5))
    )
    assert tyro.cli(
        DefaultInstanceSubparser,
        args=["bc:default-instance-smtp-server", "--bc.z", "3"],
        default=DefaultInstanceSubparser(x=1, bc=DefaultInstanceHTTPServer(y=5)),
    ) == DefaultInstanceSubparser(x=1, bc=DefaultInstanceSMTPServer(z=3))
    assert (
        tyro.cli(
            DefaultInstanceSubparser,
            args=["--x", "1", "bc:default-instance-http-server", "--bc.y", "8"],
        )
        == tyro.cli(
            DefaultInstanceSubparser,
            args=[],
            default=DefaultInstanceSubparser(x=1, bc=DefaultInstanceHTTPServer(y=8)),
        )
        == DefaultInstanceSubparser(x=1, bc=DefaultInstanceHTTPServer(y=8))
    )

    with pytest.raises(SystemExit):
        tyro.cli(DefaultInstanceSubparser, args=["--x", "1", "b", "--bc.z", "3"])
    with pytest.raises(SystemExit):
        tyro.cli(DefaultInstanceSubparser, args=["--x", "1", "c", "--bc.y", "3"])


def test_subparser_with_default_bad() -> None:
    class DefaultHTTPServer(Struct, frozen=False):
        y: int

    class DefaultSMTPServer(Struct, frozen=False):
        z: int

    class DefaultSubparser(Struct, frozen=False):
        x: int
        bc: DefaultHTTPServer | DefaultSMTPServer = 5

    # Tolerate bad static types: https://github.com/brentyi/tyro/issues/20
    # Should give us a bunch of warnings!
    with pytest.warns(UserWarning):
        assert tyro.cli(DefaultSubparser, args=["--x", "1"]) == DefaultSubparser(
            1,
            5,  # type: ignore
        )


def test_subparser_with_default_bad_alt() -> None:
    class A(Struct, frozen=False):
        a: int

    @tyro.conf.configure(tyro.conf.subcommand(name="bbbb"))
    class B(Struct, frozen=False):
        b: int

    class C(Struct, frozen=False):
        c: int

    with pytest.warns(UserWarning):
        assert tyro.cli(
            A | Annotated[B, None],  # type: ignore
            default=C(3),
            args=["c", "--c", "2"],
        ) == C(2)


def test_optional_subparser() -> None:
    class OptionalHTTPServer(Struct, frozen=False):
        y: int

    class OptionalSMTPServer(Struct, frozen=False):
        z: int

    class OptionalSubparser(Struct, frozen=False):
        x: int
        bc: Optional[OptionalHTTPServer | OptionalSMTPServer]

    assert tyro.cli(
        OptionalSubparser, args=["--x", "1", "bc:optional-http-server", "--bc.y", "3"]
    ) == OptionalSubparser(x=1, bc=OptionalHTTPServer(y=3))
    assert tyro.cli(
        OptionalSubparser, args=["--x", "1", "bc:optional-smtp-server", "--bc.z", "3"]
    ) == OptionalSubparser(x=1, bc=OptionalSMTPServer(z=3))
    assert tyro.cli(
        OptionalSubparser, args=["--x", "1", "bc:none"]
    ) == OptionalSubparser(x=1, bc=None)

    with pytest.raises(SystemExit):
        # Wrong field.
        tyro.cli(
            OptionalSubparser,
            args=["--x", "1", "bc:optional-http-server", "--bc.z", "3"],
        )
    with pytest.raises(SystemExit):
        # Wrong field.
        tyro.cli(
            OptionalSubparser,
            args=["--x", "1", "bc:optional-smtp-server", "--bc.y", "3"],
        )


def test_post_init_default() -> None:
    class DataclassWithDynamicDefault(Struct, frozen=False):
        x: int = 3
        y: Optional[int] = None

        def __post_init__(self):
            # If unspecified, set y = x.
            if self.y is None:
                self.y = self.x

    class NoDefaultPostInitArgs(Struct, frozen=False):
        inner: DataclassWithDynamicDefault

    assert tyro.cli(
        NoDefaultPostInitArgs, args=["--inner.x", "5"]
    ).inner == DataclassWithDynamicDefault(x=5, y=5)


def test_multiple_subparsers() -> None:
    class Subcommand1(Struct):
        x: int = 0

    class Subcommand2(Struct):
        y: int = 1

    class Subcommand3(Struct):
        z: int = 2

    class MultipleSubparsers(Struct):
        a: Subcommand1 | Subcommand2 | Subcommand3
        b: Subcommand1 | Subcommand2 | Subcommand3
        c: Subcommand1 | Subcommand2 | Subcommand3

    with pytest.raises(SystemExit):
        tyro.cli(MultipleSubparsers, args=[])

    assert tyro.cli(
        MultipleSubparsers, args="a:subcommand1 b:subcommand2 c:subcommand3".split(" ")
    ) == MultipleSubparsers(Subcommand1(), Subcommand2(), Subcommand3())

    assert tyro.cli(
        MultipleSubparsers,
        args="a:subcommand1 --a.x 5 b:subcommand2 --b.y 7 c:subcommand3 --c.z 3".split(
            " "
        ),
    ) == MultipleSubparsers(Subcommand1(x=5), Subcommand2(y=7), Subcommand3(z=3))

    assert tyro.cli(
        MultipleSubparsers,
        args="a:subcommand2 --a.y 5 b:subcommand1 --b.x 7 c:subcommand3 --c.z 3".split(
            " "
        ),
    ) == MultipleSubparsers(Subcommand2(y=5), Subcommand1(x=7), Subcommand3(z=3))

    assert tyro.cli(
        MultipleSubparsers,
        args="a:subcommand3 --a.z 5 b:subcommand1 --b.x 7 c:subcommand3 --c.z 3".split(
            " "
        ),
    ) == MultipleSubparsers(Subcommand3(z=5), Subcommand1(x=7), Subcommand3(z=3))


def test_multiple_subparsers_with_default() -> None:
    class Subcommand1(Struct):
        x: int = 0

    class Subcommand2(Struct):
        y: int = 1

    class Subcommand3(Struct):
        z: int = 2

    class MultipleSubparsers(Struct):
        a: Subcommand1 | Subcommand2 | Subcommand3 = Subcommand1(tyro.MISSING)
        b: Subcommand1 | Subcommand2 | Subcommand3 = Subcommand2(7)
        c: Subcommand1 | Subcommand2 | Subcommand3 = Subcommand3(3)

    with pytest.raises(SystemExit):
        tyro.cli(
            MultipleSubparsers,
            args=[],
        )

    assert tyro.cli(
        MultipleSubparsers,
        args=["a:subcommand1", "--a.x", "5"],
    ) == MultipleSubparsers(Subcommand1(x=5), Subcommand2(y=7), Subcommand3(z=3))

    assert tyro.cli(
        MultipleSubparsers,
        args="a:subcommand1 --a.x 3".split(" "),
    ) == MultipleSubparsers(Subcommand1(x=3), Subcommand2(y=7), Subcommand3(z=3))

    with pytest.raises(SystemExit):
        tyro.cli(
            MultipleSubparsers,
            args=[],
            default=MultipleSubparsers(
                Subcommand1(),
                Subcommand2(),
                Subcommand3(tyro.MISSING),
            ),
        )
    with pytest.raises(SystemExit):
        tyro.cli(
            MultipleSubparsers,
            args=[
                "a:subcommand1",
            ],
            default=MultipleSubparsers(
                Subcommand1(),
                Subcommand2(),
                Subcommand3(tyro.MISSING),
            ),
        )
    with pytest.raises(SystemExit):
        tyro.cli(
            MultipleSubparsers,
            args=["a:subcommand1", "b:subcommand2"],
            default=MultipleSubparsers(
                Subcommand1(),
                Subcommand2(),
                Subcommand3(tyro.MISSING),
            ),
        )
    with pytest.raises(SystemExit):
        tyro.cli(
            MultipleSubparsers,
            args=["a:subcommand1", "b:subcommand2", "c:subcommand3"],
            default=MultipleSubparsers(
                Subcommand1(),
                Subcommand2(),
                Subcommand3(tyro.MISSING),
            ),
        )
    assert tyro.cli(
        MultipleSubparsers,
        args=["a:subcommand1", "b:subcommand2", "c:subcommand3", "--c.z", "3"],
        default=MultipleSubparsers(
            Subcommand1(),
            Subcommand2(),
            Subcommand3(tyro.MISSING),
        ),
    ) == MultipleSubparsers(Subcommand1(x=0), Subcommand2(y=1), Subcommand3(z=3))
    assert tyro.cli(
        MultipleSubparsers,
        args=["a:subcommand1", "b:subcommand2", "c:subcommand2"],
        default=MultipleSubparsers(
            Subcommand1(),
            Subcommand2(),
            Subcommand3(tyro.MISSING),
        ),
    ) == MultipleSubparsers(Subcommand1(x=0), Subcommand2(y=1), Subcommand2(y=1))


def test_nested_subparsers_with_default() -> None:
    class Subcommand1(Struct):
        x: int = 0

    class Subcommand3(Struct):
        z: int = 2

    class Subcommand2(Struct):
        y: Subcommand1 | Subcommand3

    class MultipleSubparsers(Struct):
        a: Subcommand1 | Subcommand2 = Subcommand2(Subcommand1(tyro.MISSING))

    with pytest.raises(SystemExit):
        tyro.cli(MultipleSubparsers, args=[])
    with pytest.raises(SystemExit):
        tyro.cli(MultipleSubparsers, args=["a:subcommand2"])

    assert tyro.cli(
        MultipleSubparsers, args="a:subcommand1 --a.x 3".split(" ")
    ) == MultipleSubparsers(Subcommand1(3))
    assert tyro.cli(
        MultipleSubparsers, args="a:subcommand2 a.y:subcommand3 --a.y.z 2".split(" ")
    ) == MultipleSubparsers(Subcommand2(Subcommand3()))
    assert tyro.cli(
        MultipleSubparsers, args="a:subcommand2 a.y:subcommand3 --a.y.z 7".split(" ")
    ) == MultipleSubparsers(Subcommand2(Subcommand3(7)))
    assert tyro.cli(
        MultipleSubparsers, args="a:subcommand2 a.y:subcommand1 --a.y.x 7".split(" ")
    ) == MultipleSubparsers(Subcommand2(Subcommand1(7)))


def test_nested_subparsers_multiple() -> None:
    class Subcommand1(Struct):
        x: int = 0

    class Subcommand3(Struct):
        z: int = 2

    class Subcommand2(Struct):
        y: Subcommand1 | Subcommand3

    class MultipleSubparsers(Struct):
        a: Subcommand1 | Subcommand2
        b: Subcommand1 | Subcommand2

    with pytest.raises(SystemExit):
        tyro.cli(MultipleSubparsers, args=[])
    assert tyro.cli(
        MultipleSubparsers, args="a:subcommand1 b:subcommand1".split(" ")
    ) == MultipleSubparsers(Subcommand1(), Subcommand1())
    assert tyro.cli(
        MultipleSubparsers,
        args="a:subcommand1 b:subcommand2 b.y:subcommand1".split(" "),
    ) == MultipleSubparsers(Subcommand1(), Subcommand2(Subcommand1()))
    assert tyro.cli(
        MultipleSubparsers,
        args="a:subcommand2 a.y:subcommand1 b:subcommand2 b.y:subcommand1".split(" "),
    ) == MultipleSubparsers(Subcommand2(Subcommand1()), Subcommand2(Subcommand1()))
    assert tyro.cli(
        MultipleSubparsers,
        args=(
            "a:subcommand2 a.y:subcommand1 --a.y.x 3 b:subcommand2 b.y:subcommand1"
            " --b.y.x 7".split(" ")
        ),
    ) == MultipleSubparsers(Subcommand2(Subcommand1(3)), Subcommand2(Subcommand1(7)))


def test_nested_subparsers_multiple_in_container() -> None:
    class Subcommand1(Struct):
        x: int = 0

    class Subcommand3(Struct):
        z: int = 2

    class Subcommand2(Struct):
        y: Subcommand1 | Subcommand3

    class MultipleSubparsers(Struct):
        a: Subcommand1 | Subcommand2
        b: Subcommand1 | Subcommand2

    class Root(Struct):
        inner: MultipleSubparsers

    with pytest.raises(SystemExit):
        tyro.cli(Root, args=[])
    assert tyro.cli(
        Root, args="inner.a:subcommand1 inner.b:subcommand1".split(" ")
    ) == Root(MultipleSubparsers(Subcommand1(), Subcommand1()))
    assert tyro.cli(
        Root,
        args="inner.a:subcommand1 inner.b:subcommand2 inner.b.y:subcommand1".split(" "),
    ) == Root(MultipleSubparsers(Subcommand1(), Subcommand2(Subcommand1())))
    assert tyro.cli(
        Root,
        args=(
            "inner.a:subcommand2 inner.a.y:subcommand1 inner.b:subcommand2"
            " inner.b.y:subcommand1".split(" ")
        ),
    ) == Root(
        MultipleSubparsers(Subcommand2(Subcommand1()), Subcommand2(Subcommand1()))
    )
    assert tyro.cli(
        Root,
        args=(
            "inner.a:subcommand2 inner.a.y:subcommand1 --inner.a.y.x 3"
            " inner.b:subcommand2 inner.b.y:subcommand1 --inner.b.y.x 7".split(" ")
        ),
    ) == Root(
        MultipleSubparsers(Subcommand2(Subcommand1(3)), Subcommand2(Subcommand1(7)))
    )


def test_tuple_nesting() -> None:
    class Color(Struct):
        r: int
        g: int
        b: int

    class Location(Struct):
        x: float
        y: float
        z: float

    def main(x: Tuple[Tuple[Color], Location, float]):
        return x

    assert tyro.cli(
        main,
        args=(
            "--x.0.0.r 255 --x.0.0.g 0 --x.0.0.b 0 --x.1.x 5.0 --x.1.y 0.0"
            " --x.1.z 2.0 --x.2 4.0".split(" ")
        ),
    ) == ((Color(255, 0, 0),), Location(5.0, 0.0, 2.0), 4.0)


def test_tuple_nesting_union() -> None:
    class Color(Struct):
        r: int
        g: int
        b: int

    class Location(Struct):
        x: float
        y: float
        z: float

    def main(x: Tuple[Tuple[Color], Location, float] | Tuple[Color, Color]):
        return x

    assert tyro.cli(
        main,
        args=(
            "x:tuple-tuple-color-location-float --x.0.0.r 255 --x.0.0.g 0 --x.0.0.b 0"
            " --x.1.x 5.0 --x.1.y 0.0 --x.1.z 2.0 --x.2 4.0".split(" ")
        ),
    ) == ((Color(255, 0, 0),), Location(5.0, 0.0, 2.0), 4.0)


def test_generic_subparsers() -> None:
    T = TypeVar("T")

    class A(Struct, Generic[T], frozen=False):
        x: T

    def main(x: A[int] | A[float]) -> Any:
        return x

    assert tyro.cli(main, args="x:a-float --x.x 3.2".split(" ")) == A(3.2)
    assert tyro.cli(main, args="x:a-int --x.x 3".split(" ")) == A(3)

    def main_with_default(x: A[str] | A[int] = A(5)) -> Any:
        return x

    assert tyro.cli(main_with_default, args=[]) == A(5)
    assert tyro.cli(main_with_default, args=["x:a-str", "--x.x", "3"]) == A("3")


def test_generic_inherited() -> None:
    class UnrelatedParentClass:
        pass

    T = TypeVar("T")

    class ActualParentClass(Struct, Generic[T], frozen=False):
        x: T  # Documentation 1

        # Documentation 2
        y: T

        z: T = 3  # type: ignore
        """Documentation 3"""

    class ChildClass(UnrelatedParentClass, ActualParentClass[int], frozen=False):
        pass

    assert tyro.cli(
        ChildClass, args=["--x", "1", "--y", "2", "--z", "3"]
    ) == ChildClass(x=1, y=2, z=3)


def test_subparser_in_nested() -> None:
    class A(Struct, frozen=False):
        a: int

    class B(Struct, frozen=False):
        b: int

    class Nested2(Struct, frozen=False):
        subcommand: A | B

    class Nested1(Struct, frozen=False):
        nested2: Nested2

    class Parent(Struct, frozen=False):
        nested1: Nested1

    assert tyro.cli(
        Parent,
        args="nested1.nested2.subcommand:a --nested1.nested2.subcommand.a 3".split(" "),
    ) == Parent(Nested1(Nested2(A(3))))
    assert tyro.cli(
        Parent,
        args="nested1.nested2.subcommand:b --nested1.nested2.subcommand.b 7".split(" "),
    ) == Parent(Nested1(Nested2(B(7))))


# def test_frozen_dict() -> None:
#     def main(
#         x: Mapping[str, float] = frozendict(  # type: ignore
#             {
#                 "num_epochs": 20,
#                 "batch_size": 64,
#             }
#         ),
#     ):
#         return x
#
#     assert hash(tyro.cli(main, args="--x.num-epochs 10".split(" "))) == hash(
#         frozendict({"num_epochs": 10, "batch_size": 64})  # type: ignore
#     )


def test_nested_in_subparser() -> None:
    # https://github.com/brentyi/tyro/issues/9
    class Subtype(Struct):
        data: int = 1

    class TypeA(Struct):
        subtype: Subtype = Subtype(1)

    class TypeB(Struct):
        subtype: Subtype = Subtype(2)

    class Wrapper(Struct):
        supertype: TypeA | TypeB = TypeA()

    assert tyro.cli(Wrapper, args=[]) == Wrapper()
    assert (
        tyro.cli(Wrapper, args="supertype:type-a --supertype.subtype.data 1".split(" "))
        == Wrapper()
    )


def test_nested_in_subparser_override_with_default() -> None:
    class Mnist(Struct):
        binary: bool = False
        """Set to load binary version of MNIST dataset."""

    class ImageNet(Struct, frozen=False):
        subset: Literal[50, 100, 1000]
        """Choose between ImageNet-50, ImageNet-100, ImageNet-1000, etc."""

    # Possible optimizer configurations.

    Selector = tyro.extras.subcommand_type_from_defaults(
        {
            "m": Mnist(),
            "i": ImageNet(50),
        }
    )

    class DatasetContainer(Struct):
        dataset: Selector = Mnist()  # type: ignore

    class Adam(Struct, frozen=False):
        learning_rate: float = 1e-3
        betas: Tuple[float, float] = (0.9, 0.999)
        container: DatasetContainer = DatasetContainer()

    class Sgd(Struct, frozen=False):
        learning_rate: float = 3e-4
        container: DatasetContainer = DatasetContainer()

    # Train script.

    Optimizers = tyro.extras.subcommand_type_from_defaults(
        {"adam": Adam(container=DatasetContainer(ImageNet(50))), "sgd": Sgd()},
        prefix_names=False,
    )

    @tyro.conf.configure(tyro.conf.OmitSubcommandPrefixes)
    def train(
        optimizer: Optimizers = Adam(container=DatasetContainer(ImageNet(50))),  # type: ignore
    ) -> Adam | Sgd:
        return optimizer

    assert tyro.cli(train, args=[]) == Adam(container=DatasetContainer(ImageNet(50)))
    assert tyro.cli(train, args=["adam"]) == Adam(
        container=DatasetContainer(ImageNet(50))
    )
    assert tyro.cli(train, args=["sgd"]) == Sgd(container=DatasetContainer(Mnist()))


def test_underscore_prefix() -> None:
    """https://github.com/brentyi/tyro/issues/77"""

    class PrivateConfig(Struct, frozen=False):
        pass

    class BaseConfig(Struct, frozen=False):
        _private: PrivateConfig = PrivateConfig()

    class Level1(BaseConfig, frozen=False):
        pass

    class Level2(BaseConfig, frozen=False):
        child: Level1 = Level1()

    class Level3(BaseConfig, frozen=False):
        child: Level2 = Level2()

    tyro.cli(Level3, args=[])


def test_subcommand_dict_helper() -> None:
    def checkout(branch: str) -> str:
        """Check out a branch."""
        return branch

    def commit(message: str, all: bool = False) -> Tuple[str, bool]:
        """Make a commit."""
        return (message, all)

    assert tyro.extras.subcommand_cli_from_dict(
        {
            "commit": commit,
        },
        args="commit --message hello --all".split(" "),
    ) == ("hello", True)
    assert (
        tyro.extras.subcommand_cli_from_dict(
            {
                "checkout": checkout,
                "commit": commit,
            },
            args="checkout --branch main".split(" "),
        )
        == "main"
    )
    assert tyro.extras.subcommand_cli_from_dict(
        {
            "checkout": checkout,
            "commit": commit,
        },
        args="commit --message hello".split(" "),
    ) == ("hello", False)
    assert tyro.extras.subcommand_cli_from_dict(
        {
            "checkout": checkout,
            "commit": commit,
        },
        args="commit --message hello --all".split(" "),
    ) == ("hello", True)


def test_subcommand_by_type_tree() -> None:
    class A(Struct, frozen=False):
        a: int | str

    class Args(Struct, frozen=False):
        inner: Annotated[A, tyro.conf.subcommand(name="alt", default=A(5))] | A = A(
            "hello"
        )

    assert tyro.cli(Args, args=[]) == Args(A("hello"))
    assert "default: inner:alt" in get_helptext_with_checks(Args)


def test_annotated_narrow_0() -> None:
    class A(Struct, frozen=False): ...

    class B(A, frozen=False):
        x: int

    def main(x: Annotated[A, tyro.conf.OmitArgPrefixes] = B(x=3)) -> Any:
        return x

    assert tyro.cli(main, args=[]) == B(x=3)
    assert tyro.cli(main, args="--x 5".split(" ")) == B(x=5)


def test_annotated_narrow_1() -> None:
    class A(Struct, frozen=False): ...

    class B(A, frozen=False):
        x: int

    from tyro._resolver import narrow_subtypes

    assert narrow_subtypes(Annotated[A, False], B(3)) == Annotated[B, False]  # type: ignore


def test_union_with_dict() -> None:
    class Config(Struct, frozen=False):
        name: str
        age: int

    def main(config: Config | dict = {"name": "hello", "age": 25}) -> Any:
        return config

    assert tyro.cli(main, args=[]) == {"name": "hello", "age": 25}
    assert tyro.cli(main, args="config:dict".split(" ")) == {"name": "hello", "age": 25}
    assert tyro.cli(main, args="config:dict --config.age 27".split(" ")) == {
        "name": "hello",
        "age": 27,
    }
    assert tyro.cli(
        main, args="config:config --config.name world --config.age 27".split(" ")
    ) == Config(name="world", age=27)


def test_union_with_tuple() -> None:
    class Config(Struct, frozen=False):
        name: str
        age: int

    def main(config: Config | tuple = ("hello", 5)) -> Any:
        return config

    assert tyro.cli(main, args=[]) == ("hello", 5)
    assert tyro.cli(main, args="config:tuple".split(" ")) == ("hello", 5)
    assert tyro.cli(main, args="config:tuple hello 27".split(" ")) == ("hello", 27)
    assert tyro.cli(
        main, args="config:config --config.name world --config.age 27".split(" ")
    ) == Config(name="world", age=27)


def test_union_with_tuple_subscripted() -> None:
    class Config(Struct, frozen=False):
        name: str
        age: int

    def main(config: Config | Tuple[str, int] = ("hello", 5)) -> Any:
        return config

    assert tyro.cli(main, args=[]) == ("hello", 5)
    assert tyro.cli(main, args="config:tuple-str-int".split(" ")) == ("hello", 5)
    assert tyro.cli(main, args="config:tuple-str-int hello 27".split(" ")) == (
        "hello",
        27,
    )
    assert tyro.cli(
        main, args="config:config --config.name world --config.age 27".split(" ")
    ) == Config(name="world", age=27)


def test_union_with_tuple_autoexpand() -> None:
    class Config(Struct, frozen=False):
        name: str
        age: int

    # tyro should automatically expand this `Config` type to `Config | tuple`.
    def main(config: Config = ("hello", 5)) -> Any:  # type: ignore
        return config

    assert tyro.cli(main, args=[]) == ("hello", 5)
    assert tyro.cli(main, args="config:tuple".split(" ")) == ("hello", 5)
    assert tyro.cli(main, args="config:tuple hello 27".split(" ")) == ("hello", 27)
    assert tyro.cli(
        main, args="config:config --config.name world --config.age 27".split(" ")
    ) == Config(name="world", age=27)


def test_union_with_tuple_autoexpand_annotated() -> None:
    class Config(Struct, frozen=False):
        name: str
        age: int

    # tyro should automatically expand this `Config` type to `Config | tuple`.
    def main(
        config: Annotated[Config, tyro.conf.FlagConversionOff] = ("hello", 5),  # type: ignore
    ) -> Any:
        return config

    assert tyro.cli(main, args=[]) == ("hello", 5)
    assert tyro.cli(main, args="config:tuple".split(" ")) == ("hello", 5)
    assert tyro.cli(main, args="config:tuple hello 27".split(" ")) == ("hello", 27)
    assert tyro.cli(
        main, args="config:config --config.name world --config.age 27".split(" ")
    ) == Config(name="world", age=27)


def test_subcommand_default_with_conf_annotation() -> None:
    """Adapted from @mirceamironenco.

    https://github.com/brentyi/tyro/issues/221#issuecomment-2572850582
    """

    class OptimizerConfig(Struct):
        lr: float = 1e-1

    class AdamConfig(OptimizerConfig):
        adam_foo: float = 1.0

    class SGDConfig(OptimizerConfig):
        sgd_foo: float = 1.0

    def _constructor() -> Any:
        cfgs = [
            Annotated[SGDConfig, tyro.conf.subcommand(name="sgd")],
            Annotated[AdamConfig, tyro.conf.subcommand(name="adam")],
        ]
        # Python 3.14+ requires different approach for Union construction from tuple
        import typing

        if sys.version_info >= (3, 14) and hasattr(typing, "_UnionGenericAlias"):
            # Python 3.14: construct using internal API or use | operator chain
            import operator
            from functools import reduce

            return reduce(operator.or_, cfgs)  # type: ignore
        else:
            return getattr(Union, "__getitem__")(tuple(cfgs))  # type: ignore

    class Config1(Struct):
        optimizer: Annotated[
            OptimizerConfig, tyro.conf.arg(constructor_factory=_constructor)
        ] = AdamConfig()
        foo: int = 1
        bar: str = "abc"

    assert "(default: optimizer:adam)" in get_helptext_with_checks(Config1)

    class Config2(Struct):
        optimizer: Annotated[
            OptimizerConfig, tyro.conf.arg(constructor_factory=_constructor)
        ] = SGDConfig()
        foo: int = 1
        bar: str = "abc"

    assert "(default: optimizer:sgd)" in get_helptext_with_checks(Config2)


def test_subcommand_dict_helper_with_pydantic_basemodel() -> None:
    """Test that subcommand names from dictionary keys are preserved for Pydantic BaseModel classes.

    This is a regression test for https://github.com/brentyi/tyro/issues/321
    where Pydantic BaseModel subcommands were not using the dictionary key as
    the subcommand name.
    """
    if tyro._experimental_options["backend"] == "argparse":
        pytest.skip("Running in argparse backend")

    try:
        from pydantic import BaseModel, Field
    except ImportError:
        pytest.skip("pydantic not installed")
        return

    def first_command(a: int) -> None:
        """Check out a branch."""
        print(f"{a=}")

    class SecondCommand(Struct, frozen=False):
        a: int

    # Pydantic dataclass
    class ThirdCommand(Struct, frozen=False):
        a: int = 3

    # Pydantic BaseModel - this was the failing case
    class FourthCommand(BaseModel):
        a: int = Field(3)

    # Test that helptext shows the correct subcommand names
    target = io.StringIO()
    with pytest.raises(SystemExit), contextlib.redirect_stdout(target):
        tyro.extras.subcommand_cli_from_dict(
            {
                "my-first": first_command,
                "my-second": SecondCommand,
                "my-third": ThirdCommand,
                "my-fourth": FourthCommand,
            },
            args=["--help"],
        )

    helptext = target.getvalue()

    # Check that all custom subcommand names appear in the help text
    assert "my-first" in helptext
    assert "my-second" in helptext
    assert "my-third" in helptext
    assert "my-fourth" in helptext  # This was failing before the fix

    # Verify the subcommand names work when parsing
    assert tyro.extras.subcommand_cli_from_dict(
        {
            "my-first": first_command,
            "my-second": SecondCommand,
            "my-third": ThirdCommand,
            "my-fourth": FourthCommand,
        },
        args=["my-second", "--a", "5"],
    ) == SecondCommand(a=5)

    # Test the Pydantic BaseModel case specifically
    result = tyro.extras.subcommand_cli_from_dict(
        {
            "my-first": first_command,
            "my-second": SecondCommand,
            "my-third": ThirdCommand,
            "my-fourth": FourthCommand,
        },
        args=["my-fourth", "--a", "7"],
    )
    assert isinstance(result, FourthCommand)
    assert result.a == 7


def test_nargs_then_subcommand() -> None:
    """Test that nargs='*' arguments can be followed by subcommands.

    This is not supported by the argparse backend due to argparse's greedy
    consumption of variable-length arguments. This test is intended for the
    tyro backend which will support flexible argument ordering.
    """
    # Skip this test when using argparse backend.

    if tyro._experimental_options["backend"] == "argparse":
        pytest.skip("nargs followed by subcommands not supported in argparse backend")

    class SubconfigA(Struct, frozen=False):
        pass

    class SubconfigB(Struct, frozen=False):
        pass

    class Config(Struct, frozen=False):
        x: List[str]
        y: SubconfigA | SubconfigB

    assert tyro.cli(Config, args=["--x", "a", "b", "c", "y:subconfig-a"]) == Config(
        ["a", "b", "c"], SubconfigA()
    )
