# mypy: ignore-errors
from typing import Any, Generic, Protocol, Type, TypeVar, runtime_checkable

from salix import Struct

import tyro

OutT_co = TypeVar("OutT_co", covariant=True)


@runtime_checkable
class BuilderProtocol(Protocol[OutT_co]):
    def build(self, **kwd_override: Any) -> OutT_co: ...


OutT = TypeVar("OutT")


class SomeConfig(Generic[OutT]):
    _target: Type[OutT]

    def _configure(self) -> OutT:
        raise NotImplementedError


class Foo: ...


class RealConfig(Struct, SomeConfig[Foo], frozen=False):
    bar: str = "foo_bar"

    def build(self, **kwd_override: Any) -> Foo:
        return Foo()


def test_protocol_typevar() -> None:
    """Adapted from: https://github.com/brentyi/tyro/issues/335"""
    assert isinstance(RealConfig(), BuilderProtocol)
    expected = RealConfig(bar="baz")
    assert tyro.cli(RealConfig, args=["--bar", "baz"]) == expected


test_protocol_typevar()
