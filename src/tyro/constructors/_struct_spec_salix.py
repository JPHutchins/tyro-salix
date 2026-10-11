from __future__ import annotations

import functools
from typing import Any, cast

import salix

from .. import _docstrings, _resolver
from .._singleton import (
    MISSING,
    MISSING_NONPROP,
    is_missing,
)
from ._struct_spec import StructConstructorSpec, StructFieldSpec, StructTypeInfo


def _get_struct_field_default(
    field: _resolver.ResolvedField, parent_default_instance: Any
) -> Any:
    if parent_default_instance is MISSING:
        return MISSING

    if not is_missing(parent_default_instance) and parent_default_instance is not None:
        if hasattr(parent_default_instance, field.name):
            return getattr(parent_default_instance, field.name)

    if field.default is not salix.MISSING:
        return field.default

    return MISSING_NONPROP


def salix_struct_rule(info: StructTypeInfo) -> StructConstructorSpec | None:
    if not _resolver.is_salix_struct(info.type):
        return None

    field_list = [
        StructFieldSpec(
            name=struct_field.name,
            type=cast(Any, struct_field.type),
            default=_get_struct_field_default(struct_field, info.default),
            helptext=functools.partial(
                _docstrings.get_field_docstring,
                info.type,
                struct_field.name,
                info.markers,
            ),
        )
        for struct_field in _resolver.resolved_fields(info.type)
    ]
    return StructConstructorSpec(instantiate=info.type, fields=tuple(field_list))
