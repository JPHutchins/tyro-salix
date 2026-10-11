"""Salix Struct support."""

from typing import Any

from salix import Struct

_SalixStructMeta = type(Struct)


def is_struct(cls: Any) -> bool:
    return isinstance(cls, _SalixStructMeta)


def is_salix_base(cls: Any) -> bool:
    return getattr(cls, "__module__", None) == "salix"


def is_struct_instance(obj: Any) -> bool:
    return isinstance(obj, Struct)
