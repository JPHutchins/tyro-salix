"""Salix Struct support: read Structs wherever dataclasses are read."""

import dataclasses
import weakref
from typing import Any, Dict, List, Tuple, Type

try:
    import salix
    from salix import Struct as SalixStruct  # type: ignore

    _SalixStructMeta: Any = type(SalixStruct)
except ImportError:
    SalixStruct = None  # type: ignore
    _SalixStructMeta = ()


def is_struct(cls: Any) -> bool:
    return isinstance(cls, _SalixStructMeta)


def is_salix_base(cls: Any) -> bool:
    return getattr(cls, "__module__", None) == "salix"


def _as_dataclass_field(field: Any) -> dataclasses.Field:
    synthesized = dataclasses.Field(
        default=(
            dataclasses.MISSING
            if field.default is salix.MISSING
            else field.default
        ),
        default_factory=dataclasses.MISSING,
        init=field.init,
        repr=field.repr,
        hash=field.hash,
        compare=field.compare,
        metadata=dict(field.metadata),
        kw_only=field.kw_only,
        **(
            {"doc": None}
            if "doc" in dataclasses.Field.__init__.__code__.co_varnames
            else {}
        ),
    )
    synthesized.name = field.name
    synthesized.type = field.type
    return synthesized


_struct_fields_by_class: "weakref.WeakKeyDictionary[Type, Tuple[dataclasses.Field, ...]]" = (
    weakref.WeakKeyDictionary()
)


def struct_fields(cls: Type) -> List[dataclasses.Field]:
    if cls not in _struct_fields_by_class:
        _struct_fields_by_class[cls] = tuple(
            _as_dataclass_field(field) for field in salix.fields(cls)
        )
    return list(_struct_fields_by_class[cls])


def resolved_fields(cls: Type) -> List[dataclasses.Field]:
    """Fields for a class, whether dataclass or Struct."""
    if is_struct(cls):
        return struct_fields(cls)
    return dataclasses.fields(cls)


def fields_of(cls_or_instance: Any) -> List[dataclasses.Field]:
    if is_struct(cls_or_instance):
        return struct_fields(cls_or_instance)
    cls = cls_or_instance if isinstance(cls_or_instance, type) else type(cls_or_instance)
    if is_struct(cls):
        return struct_fields(cls)
    return dataclasses.fields(cls_or_instance)
