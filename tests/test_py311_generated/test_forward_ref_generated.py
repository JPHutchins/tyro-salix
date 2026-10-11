from typing import Union

import pytest
from salix import Struct

import tyro


class A1(Struct, frozen=False):
    x: int
    bc: "B| C"


class A2(Struct, frozen=False):
    x: int
    bc: Union["B", "C"]


class B(Struct, frozen=False):
    y: "int"


class C(Struct, frozen=False):
    z: int


def test_forward_ref_1():
    assert tyro.cli(A1, args=["--x", "1", "bc:b", "--bc.y", "3"]) == A1(x=1, bc=B(y=3))
    assert tyro.cli(A1, args=["--x", "1", "bc:c", "--bc.z", "3"]) == A1(x=1, bc=C(z=3))

    with pytest.raises(SystemExit):
        tyro.cli(A1, args=["--x", "1", "bc:b", "--bc.z", "3"])
    with pytest.raises(SystemExit):
        tyro.cli(A1, args=["--x", "1", "bc:c", "--bc.y", "3"])


def test_forward_ref_2():
    assert tyro.cli(A2, args=["--x", "1", "bc:b", "--bc.y", "3"]) == A2(x=1, bc=B(y=3))
    assert tyro.cli(A2, args=["--x", "1", "bc:c", "--bc.z", "3"]) == A2(x=1, bc=C(z=3))

    with pytest.raises(SystemExit):
        tyro.cli(A2, args=["--x", "1", "bc:b", "--bc.z", "3"])
    with pytest.raises(SystemExit):
        tyro.cli(A2, args=["--x", "1", "bc:c", "--bc.y", "3"])
