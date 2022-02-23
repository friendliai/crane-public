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


"""Descriptors.

Issues:
- mypy lacks support on __get__ and __set__
  https://github.com/python/mypy/issues/6185

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from typing_extensions import Protocol

# cached_property supported natively since python 3.8
try:
    # pylint: disable=unused-import
    from functools import cached_property  # type: ignore
except ImportError:

    # mypy does not support decorated properties.
    if TYPE_CHECKING:
        # pylint: disable=invalid-name
        cached_property = property  # type: ignore  # noqa: F811
    else:

        class cached:  # pylint: disable=invalid-name
            """Cache decorator.

            Wraps around a descriptor and caches the output.
            Note that the descriptor should be read only.

            Inspired from django

            >>> class A:
                    @cached
                    @property
                    def method(self):
                        print('called')
                        return 1

            >>> a = A()
            >>> a.method
                called
                1
            >>> a.method
                1

            """

            def __init__(self, descriptor: DescriptorProtocol) -> None:
                """Wrap descriptor."""
                self.descriptor = descriptor
                self.__doc__ = getattr(descriptor, "__doc__")
                self.name: str | None = None

            def __get__(self, obj: T | None, objtype: type[T]) -> Any:
                """Evaluate descriptor and switch descriptor with result value."""
                assert self.name, "property should be bound."
                ref = obj if obj is not None else objtype
                res = self.descriptor.__get__(obj, objtype)
                setattr(ref, self.name, res)
                return res

            def __set_name__(self, objtype: type[T], name: str) -> None:
                """Assign this descriptor to a class."""
                self.name = name

        def cached_property(func):  # type: ignore
            """Export cached property."""
            return cached(property(func))


T = TypeVar("T")


class DescriptorProtocol(Protocol):
    """An object that implements __get__ is an descriptor."""

    def __get__(self, obj: T | None, objtype: type[T]) -> Any:
        """Get this attribute."""


class LazyAttribute(Generic[T]):
    """A lazy attribute that is set after creating the instance.

    The attribute should be set a value before reading.
    """

    def __init__(self) -> None:
        """Initialize."""
        self._name: str | None = None

    def __get__(self, obj: object | None, objtype: type) -> T:
        """Read value from data."""
        raise RuntimeError(f"Lazy attribute({self._name}) on {objtype} not set.")

    def __set_name__(self, owner, name: str) -> None:
        """Set attribute name."""
        self._name = name
