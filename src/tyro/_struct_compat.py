"""Salix Struct support: read Structs wherever dataclasses are read."""

import dataclasses
from typing import Any, Dict, List, Type

try:
    from salix import Struct as SalixStruct  # type: ignore
except ImportError:
    SalixStruct = None  # type: ignore


def is_struct(cls: Any) -> bool:
    return (
        SalixStruct is not None
        and (type(cls) is type or type(cls) is type(SalixStruct))
        and issubclass(cls, SalixStruct)
    )


def struct_fields(cls: Type) -> List[dataclasses.Field]:
    names = cls.__struct_fields__  # type: ignore[attr-defined]
    annotations = cls.__struct_annotations__  # type: ignore[attr-defined]
    defaults = cls.__struct_defaults__  # type: ignore[attr-defined]
    required_count = len(names) - len(defaults)
    fields = []
    for position, name in enumerate(names):
        field = dataclasses.Field(
            default=(
                dataclasses.MISSING
                if position < required_count
                else defaults[position - required_count]
            ),
            default_factory=dataclasses.MISSING,
            init=True,
            repr=True,
            hash=None,
            compare=True,
            metadata={},
            kw_only=False,
            **(
                {"doc": None}
                if "doc" in dataclasses.Field.__init__.__code__.co_varnames
                else {}
            ),
        )
        field.name = name
        field.type = annotations[position]
        fields.append(field)
    return fields


def resolved_fields(cls: Type) -> List[dataclasses.Field]:
    """Fields for a class, whether dataclass or Struct."""
    if is_struct(cls):
        return struct_fields(cls)
    return dataclasses.fields(cls)
