"""Regression tests for GitHub issues #474 and #475.

PEP 695 type parameters (``class Foo[T]: ...``, Python 3.12+) live in
``__type_params__``, not in module globals. Combined with stringized
annotations (``from __future__ import annotations`` / PEP 563), a field whose
type references such a parameter used to raise an obscure
``NameError: name 'T' is not defined`` from ``get_type_hints`` (#475). This also
surfaced through ``InitVar`` members (#474), which tyro should
recognize as ordinary constructor arguments.
"""

from __future__ import annotations

from dataclasses import InitVar

import pytest
from salix import Struct

import tyro


class Container[T](Struct, frozen=False):
    items: list[T]


class Sequencer[Data](Struct, frozen=False):
    items: list[Data]


type Seq = Sequencer[int]


class Bare[T](Struct, frozen=False):
    x: T


class Pair[K, V](Struct, frozen=False):
    k: K
    v: V


class Compound[T](Struct, frozen=False):
    mapping: dict[str, T]
    opt: T | None = None
    rest: tuple[T, ...] = ()


class Base[T](Struct, frozen=False):
    base_field: T


class Child[T](Base[T], frozen=False):
    child_field: T


class ReifiedChild(Base[int], frozen=False):
    extra: str = "x"


def test_pep695_generic_stringized_annotation_resolves() -> None:
    # #475: previously raised `NameError: name 'T' is not defined` because the
    # stringized `list[T]` annotation couldn't see the PEP 695 type parameter.
    out = tyro.cli(Container[int], args=["--items", "1", "2", "3"])
    assert out.items == [1, 2, 3]
    assert all(isinstance(x, int) for x in out.items)

    out_str = tyro.cli(Container[str], args=["--items", "a", "b"])
    assert out_str.items == ["a", "b"]


def test_initvar_is_recognized_as_constructor_arg() -> None:
    # #474: InitVar fields are init-only pseudo-fields passed to __init__ /
    # __post_init__, so tyro should expose them as CLI arguments.
    class WithInit(Struct, frozen=False):
        x: int
        offset: InitVar[int] = 10
        total: int = 0

        def __post_init__(self, offset: int) -> None:
            self.total = self.x + offset

    # If InitVar weren't recognized, `--offset` would be an unrecognized option.
    out = tyro.cli(WithInit, args=["--x", "1", "--offset", "5"])
    assert out.x == 1
    assert out.total == 6
    # Default is used when not provided.
    assert tyro.cli(WithInit, args=["--x", "2"]).total == 12


def test_initvar_of_pep695_generic_does_not_crash() -> None:
    # The exact shape from the issue: an InitVar of a (PEP 695) generic, behind
    # a PEP 695 `type` alias, with stringized annotations. Used to raise the
    # obscure NameError; should now resolve cleanly.
    class App(Struct, frozen=False):
        name: str = "default"
        _sequencer: InitVar[Seq | None] = None
        seq: Seq | None = None

        def __post_init__(self, _sequencer: Seq | None) -> None:
            self.seq = _sequencer

    out = tyro.cli(App, args=["--name", "hi"])
    assert out.name == "hi"
    assert out.seq is None


def test_pep695_multiple_params_and_compound_refs() -> None:
    # Multiple PEP 695 params, and type params nested inside dict/Optional/tuple.
    assert tyro.cli(Pair[int, str], args=["--k", "1", "--v", "a"]) == Pair(1, "a")

    out = tyro.cli(
        Compound[int],
        args=["--mapping", "a", "1", "--opt", "2", "--rest", "3", "4"],
    )
    assert out.mapping == {"a": 1}
    assert out.opt == 2 and isinstance(out.opt, int)
    assert out.rest == (3, 4)
    # Defaults still work when the param-typed optionals are omitted.
    assert tyro.cli(Compound[str], args=["--mapping", "k", "v"]) == Compound(
        {"k": "v"}, None, ()
    )


def test_pep695_inheritance() -> None:
    # Type parameter forwarded through a base class: Child[int] -> Base[int].
    assert tyro.cli(
        Child[int], args=["--base-field", "1", "--child-field", "2"]
    ) == Child(base_field=1, child_field=2)
    # Base reified at the inheritance site: ReifiedChild(Base[int]).
    out = tyro.cli(ReifiedChild, args=["--base-field", "9"])
    assert out.base_field == 9 and isinstance(out.base_field, int)
    assert out.extra == "x"


def test_pep695_generic_as_nested_field() -> None:
    class Outer(Struct, frozen=False):
        inner: Bare[int]

    out = tyro.cli(Outer, args=["--inner.x", "7"])
    assert out.inner == Bare(7) and isinstance(out.inner.x, int)


def test_pep695_generic_in_subcommand_union() -> None:
    class Outer2(Struct, frozen=False):
        choice: Bare[int] | Pair[int, int]

    assert tyro.cli(Outer2, args=["choice:bare-int", "--choice.x", "3"]) == Outer2(
        choice=Bare(3)
    )
    assert tyro.cli(
        Outer2, args=["choice:pair-int-int", "--choice.k", "1", "--choice.v", "2"]
    ) == Outer2(choice=Pair(1, 2))


def test_pep695_unreified_generic_gives_clean_error_not_nameerror() -> None:
    # An *unparameterized* PEP 695 generic field can't bind its type parameter,
    # so it resolves to `Any` -> a clean "unsupported type" error (SystemExit),
    # NOT the obscure pre-fix `NameError: name 'T' is not defined`.
    class Outer(Struct, frozen=False):
        inner: Bare

    with pytest.raises(SystemExit):
        tyro.cli(Outer, args=["--inner.x", "1"])
