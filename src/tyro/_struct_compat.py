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


def fields_of(cls_or_instance: Any) -> List[dataclasses.Field]:
    if is_struct(cls_or_instance):
        return struct_fields(cls_or_instance)
    cls = cls_or_instance if isinstance(cls_or_instance, type) else type(cls_or_instance)
    if is_struct(cls):
        return struct_fields(cls)
    return dataclasses.fields(cls_or_instance)


class struct_cached_property:
    def __init__(self, func: Any) -> None:
        self.func = func
        self.__doc__ = getattr(func, "__doc__")
        self.name = getattr(func, "__name__")
        self._cache: dict[int, tuple[Any, Any]] = {}

    def __get__(self, obj: Any, owner: Any = None) -> Any:
        if obj is None:
            return self
        key = id(obj)
        entry = self._cache.get(key)
        if entry is not None and entry[0] is obj:
            return entry[1]
        value = self.func(obj)
        self._cache[key] = (obj, value)
        return value


def replace_instance(instance: Any, **changes: Any) -> Any:
    cls = type(instance)
    if is_struct(cls):
        values = {name: getattr(instance, name) for name in cls.__struct_fields__}
        values.update(changes)
        return cls(**values)
    return dataclasses.replace(instance, **changes)
