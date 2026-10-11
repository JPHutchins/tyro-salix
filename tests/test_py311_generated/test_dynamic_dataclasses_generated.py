import pytest
from salix import Struct

import tyro


def test_dynamic():
    B = type(Struct)("B", (Struct,), {"__annotations__": {"c": int}})
    A = type(Struct)("A", (Struct,), {"__annotations__": {"b": B}})

    with pytest.raises(SystemExit):
        tyro.cli(A, args=[])
    assert tyro.cli(A, args=["--b.c", "5"]) == A(b=B(c=5))
