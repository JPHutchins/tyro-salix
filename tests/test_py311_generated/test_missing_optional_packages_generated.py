import builtins
from typing import Any

import pytest
from salix import Struct


# https://stackoverflow.com/questions/60227582/making-a-python-test-think-an-installed-package-is-not-available
@pytest.fixture
def hide_optional_packages(monkeypatch: Any) -> None:
    import_orig = builtins.__import__

    def mocked_import(name, *args, **kwargs):
        if name in ("pydantic", "flax", "omegaconf", "upath"):
            raise ImportError()
        return import_orig(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mocked_import)


def test_missing_optional_packages(hide_optional_packages: Any) -> None:
    class Extra(Struct, frozen=False):
        a: int = 3
        b: str = "5"

    def main(x: int, extra: Extra) -> int:
        del extra
        return x

    import tyro

    assert tyro.cli(main, args=["--x", "5"]) == 5
