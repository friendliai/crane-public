# Copyright (C) 2018-2021 Seoul National University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Functool utilities."""

from __future__ import annotations

import types
from asyncio import iscoroutinefunction
from dataclasses import MISSING, dataclass
from functools import update_wrapper
from inspect import Parameter, Signature, signature
from typing import Any, Callable, get_type_hints

from crane.common.util.types import get_global_namespace, get_local_namespace_of_caller

ARG_GROUP_KEY = "__ARG_GROUP__"


def arg_group(t: type) -> type:
    """Make a class into a argument group."""
    t = dataclass(t)
    setattr(t, ARG_GROUP_KEY, "")
    return t


def is_arg_group(t: type) -> bool:
    """Return true if this is a argument group."""
    return hasattr(t, ARG_GROUP_KEY)


# pylint: disable=too-many-locals
def expand_arg_group(f: Callable) -> Callable:
    """A decorator that expands argument groups into individual arguments.

    A argument group is represented as a dataclass.

    Examples:
        >>> @dataclass
            class Group:
                a: int
                b: float

        >>> @expand_arg_group
            def func(g: Group): ...

        >>> # signature of func
        >>> # def func(a: int, b: float): ...

    """
    # Parse given function arguments
    globalns = get_global_namespace(f)
    localns = get_local_namespace_of_caller()
    annotation = get_type_hints(f, globalns, dict(localns))

    # Identify argument groups
    #   argument group name to class mapping
    arg_groups = {name: arg for name, arg in annotation.items() if is_arg_group(arg)}
    #   group name to field list mapping
    group_field_mapping = {
        name: getattr(arg, "__dataclass_fields__") for name, arg in arg_groups.items()
    }

    # Create flattened signature (modify orignal signature)
    org_sig = signature(f)
    parameters = []  # new function signature parameters
    annotations = f.__annotations__  # new function annotation

    for param in org_sig.parameters.values():
        if param.name in group_field_mapping:
            del annotations[param.name]

            for field in group_field_mapping[param.name].values():
                param_kw = {
                    "name": field.name,
                    "kind": param.kind,
                    "annotation": field.type,
                }
                if field.default is not MISSING:
                    param_kw["default"] = field.default
                sub_param = Parameter(**param_kw)
                parameters.append(sub_param)
                annotations[field.name] = field.type
        else:
            parameters.append(param)

    new_sig = Signature(parameters, return_annotation=org_sig.return_annotation)

    def _group_arguments(*args, **kwargs) -> dict:
        nonlocal new_sig
        bound_args = new_sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        arguments = bound_args.arguments

        for group_name, fields in group_field_mapping.items():
            group_cls = arg_groups[group_name]
            group_args = {field: arguments.pop(field) for field in fields}
            arguments[group_name] = group_cls(**group_args)

        return arguments

    if iscoroutinefunction(f):

        @full_wraps(f)
        async def _wrapper(*args, **kwargs):
            return await f(**_group_arguments(*args, **kwargs))

    else:

        @full_wraps(f)
        def _wrapper(*args, **kwargs):
            return f(**_group_arguments(*args, **kwargs))

    setattr(_wrapper, "__annotations__", annotations)
    setattr(_wrapper, "__signature__", new_sig)

    return _wrapper


def full_wraps(wrapped: Callable) -> Callable:
    """Like functools.wraps, but also copies other metadatas.

    copy original function's __globals__ so that type annotations is happy.
    some libraries use `func.__globals__` as a namespace to evaluate forward
    references. If we do not copy the original __globals__, then type
    inference fails.

    """

    def _full_wraps(wrapper: Callable) -> Callable:
        wrapped_globals: dict[str, Any] = getattr(wrapped, "__globals__")
        wrapper_globals: dict[str, Any] = getattr(wrapper, "__globals__")
        globalns = {**wrapped_globals, **wrapper_globals}

        new_wrapper = types.FunctionType(
            wrapper.__code__,
            globalns,
            name=wrapped.__name__,
            argdefs=getattr(wrapped, "__defaults__"),
            closure=getattr(wrapper, "__closure__"),
        )

        new_wrapper = update_wrapper(new_wrapper, wrapped)
        setattr(new_wrapper, "__kwdefaults__", getattr(wrapped, "__kwdefaults__"))

        return new_wrapper

    return _full_wraps
