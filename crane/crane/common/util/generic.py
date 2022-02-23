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

"""Utilities for generic classes."""

from __future__ import annotations

from typing import Any, TypeVar

from typing_extensions import Protocol

T = TypeVar("T", bound="HasGenericArgsHook")


class HasGenericArgsHook(Protocol):
    """Defines a generic arguments hook."""

    @classmethod
    def _generic_args_hook(cls, args: tuple[Any, ...]) -> None:
        """Hook called with generic arguments as input."""


class GenericArgsHookMixin:
    """Mixin class provide a hook called with generic arguments.

    Note:
        This class should be the first base class.

    """

    @classmethod
    def __class_getitem__(cls: type[T], args: Any | tuple[Any, ...]) -> type[T]:
        """Return a child class of T that contains generic arguments as attributes."""
        if not isinstance(args, tuple):
            args = (args,)

        child_cls_name = f"{cls.__name__}_{args}"
        child_cls: type[T] = cls.__class__(child_cls_name, (cls,), {})  # type: ignore
        child_cls._generic_args_hook(args)  # pylint: disable=protected-access
        return child_cls
