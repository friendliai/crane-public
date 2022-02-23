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

"""Resource abstractions."""

from __future__ import annotations

import abc
from collections import defaultdict
from itertools import chain
from typing import (
    ClassVar,
    DefaultDict,
    Generic,
    Hashable,
    Iterator,
    Mapping,
    Type,
    TypeVar,
)

from crane.common.util.generic import GenericArgsHookMixin
from crane.common.util.itertools import value_map

R = TypeVar("R", bound="ResourceInterface")
A = TypeVar("A", bound="AbstractAllocation")

G = TypeVar("G", bound="AbstractResourceGroup")

L = TypeVar("L", bound="LogicalInterface")
P = TypeVar("P", bound="PhysicalInterface")

LRG = TypeVar("LRG", bound="AbstractLogicalResourceGroup")
PRG = TypeVar("PRG", bound="AbstractPhysicalResourceGroup")

AG = TypeVar("AG", bound="AllocationGroup")

K = TypeVar("K", bound=Hashable)


class ResourceInterface(abc.ABC):
    """Resource interface.

    All resource abstractions should implement this interface.
    """

    @classmethod
    @abc.abstractmethod
    def empty(cls: type[R]) -> R:
        """Return a empty resource.

        Returns:
            R: New empty resource

        """

    @classmethod
    def sum(cls: type[R], *resources: R) -> R:
        """Reduces list of resources to a single aggregated resource.

        Args:
            *resources (R): list of resources

        Returns:
            R: aggregated resource

        """
        return sum(resources, cls.empty())

    @abc.abstractmethod
    def __add__(self: R, other: R) -> R:
        """Add two resource units together.

        Args:
            other (R): other resource to add

        Returns:
            R: new resource object

        Raises:
            ValueError: if addition is invalid

        """

    @abc.abstractmethod
    def __sub__(self: R, other: R) -> R:
        """Subtract one resource unit from another.

        Args:
            other (R): other resource to subtract

        Returns:
            R: new resource object (self - other)

        Raises:
            ValueError: if subtraction is invalid

        """

    @abc.abstractmethod
    def __bool__(self) -> bool:
        """Return True if the resource is not empty."""

    @abc.abstractmethod
    def __lt__(self: R, other: R) -> bool:
        """Return True if other can contain self.

        a < b => a.__lt__(b)

        If `self < other`, then `other - self` should not raise an exception.
        """

    @abc.abstractmethod
    def __eq__(self, other: object) -> bool:
        """Return True if two resources are equal."""

    def __le__(self: R, other: R) -> bool:
        """Less or equal to."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__lt__(other) or self.__eq__(other)

    @abc.abstractmethod
    def __gt__(self: R, other: R) -> bool:
        """Return True if self can contain another."""

    def __ge__(self: R, other: R) -> bool:
        """Greater or equal to."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__gt__(other) or self.__eq__(other)

    def __ne__(self: R, other: object) -> bool:
        """Not Equal."""
        return not self.__eq__(other)


class AbstractAllocation(ResourceInterface, Generic[R]):
    """Resource abstraction that shows the allocation status.

    Args:
        total (R): Maximum resource that can be acquired
        released (R): Current available resource

    """

    total: R
    released: R

    def __init__(self, total: R, released: R) -> None:
        """Initialize."""
        self.total = total
        self.released = released

    def __post_init__(self) -> None:
        """Validate."""
        if not self.total >= self.released:
            raise ValueError("Released cannot be greater than total.")

    @property
    def acquired(self) -> R:
        """Return acquired."""
        return self.total - self.released

    @property
    def as_tuple(self) -> tuple[R, R, R]:
        """Return tuple of (total, acquired, released)."""
        return self.total, self.acquired, self.released

    def __add__(self: A, other: A) -> A:
        """Add two resource units together."""
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.__class__(self.total + other.total, self.released + other.released)

    def __sub__(self: A, other: A) -> A:
        """Subtract one resource unit from another."""
        if not isinstance(other, self.__class__):
            return NotImplemented

        return self.__class__(self.total - other.total, self.released - other.released)

    def __bool__(self) -> bool:
        """Return True if the resource is empty."""
        return bool(self.total)

    def __lt__(self: A, other: A) -> bool:
        """Return if other can contain self."""
        return self.as_tuple < other.as_tuple

    def __gt__(self: A, other: A) -> bool:
        """Return if self can contain other."""
        return self.as_tuple > other.as_tuple

    def __eq__(self, other: object) -> bool:
        """Return True if both total and acquired are equal."""
        if not isinstance(other, self.__class__):
            return NotImplemented

        return (self.total, self.released) == (other.total, other.released)

    def acquire(self: A, block: R) -> A:
        """Acquire a resource.

        Raises:
            ValueError: if resource cannot be acquired

        """
        return self.__class__(self.total, self.released - block)

    def release(self: A, block: R) -> A:
        """Release a resource.

        Raises:
            ValueError: if resource cannot be released

        """
        return self.__class__(self.total, self.released + block)


class AbstractResourceGroup(Mapping[K, R], ResourceInterface, Generic[K, R]):
    """A mapping of id to resources.

    Does not allow empty resource mapping (id -> resource.empty())

    Args:
        resources (Mapping[K, R]): resource mapping

    Raises:
        ValueError: if a resource is empty

    """

    resources: Mapping[K, R]

    @classmethod
    def empty(cls: type[G]) -> G:
        """Empty resource group."""
        return cls()

    def __init__(self, resources: Mapping[K, R] | None = None) -> None:
        """Initialize."""
        object.__setattr__(self, "resources", resources or {})
        if not all(self.values()):
            raise ValueError("A resource is empty.")

    def is_subset(self, other: G) -> bool:
        """Return true if the given resource is a subset of this group."""
        return self <= other

    def __add__(self: G, other: G) -> G:
        """Add two resource groups."""
        if not isinstance(other, self.__class__):
            return NotImplemented

        new_resources: DefaultDict[K, list[R]] = defaultdict(list)
        for index, resource in chain(self.items(), other.items()):
            new_resources[index].append(resource)

        new_resource = value_map(new_resources, lambda r: r[0].__class__.sum(*r))
        return self.__class__(new_resource)

    def __sub__(self: G, other: G) -> G:
        """Subtract two resource groups."""
        if not isinstance(other, self.__class__):
            return NotImplemented

        if not self.keys() >= other.keys():
            raise ValueError("Resource cannot be subtracted")

        new_resources = {}
        for index, resource in self.items():
            if index in other:
                resource = resource - other[index]

            if resource:
                new_resources[index] = resource

        return self.__class__(new_resources)

    def __lt__(self: G, other: object) -> bool:
        """Check if other contains self."""
        if not isinstance(other, (AbstractResourceGroup, self.__class__)):
            return NotImplemented

        for index, resource in self.items():
            if index not in other or not resource <= other[index]:
                return False

        if self == other:
            return False

        return True

    def __gt__(self: G, other: object) -> bool:
        """Check if self contains other."""
        if not isinstance(other, (AbstractResourceGroup, self.__class__)):
            return NotImplemented

        for index, resource in other.items():
            if index not in self or not resource <= self[index]:
                return False

        if self == other:
            return False

        return True

    def __eq__(self: G, other: object) -> bool:
        """Check if self equals other."""
        if not isinstance(other, (AbstractResourceGroup, self.__class__)):
            return NotImplemented

        if self.keys() != other.keys():
            return False

        for index in self:
            if self[index] != other[index]:
                return False

        return True

    def __getitem__(self, key: K) -> R:
        """Get element resource by key."""
        return self.resources.__getitem__(key)

    def __iter__(self) -> Iterator[K]:
        """Iterate over keys."""
        return iter(self.resources)

    def __bool__(self) -> bool:
        """Return True if the resource is empty."""
        return bool(self.resources)

    def __len__(self) -> int:
        """Return the number of _resources."""
        return len(self.resources)


class LogicalInterface(ResourceInterface):
    """A logical resource abstraction."""


class PhysicalInterface(ResourceInterface, Generic[L]):
    """Represent a unit of physical resource."""

    @abc.abstractmethod
    def as_logical(self) -> L:
        """Return a logical resource that reflect this physical resource.

        Returns:
            L: A logical resource

        """

    @abc.abstractmethod
    def __and__(self: P, other: P) -> P:
        """Returns a intersection of two physical resources.

        Args:
            other (P): The other physical resource

        Returns:
            P: common physical resource

        """


class AbstractLogicalResourceGroup(
    AbstractResourceGroup[K, L], LogicalInterface, Generic[K, L]
):
    """A group of logical resources."""


class AbstractPhysicalResourceGroup(
    GenericArgsHookMixin,
    AbstractResourceGroup[K, P],
    PhysicalInterface[LRG],
    Generic[K, P, LRG],
):
    """A group of physical resources."""

    matching_logical_cls: ClassVar[Type[LRG]]  # pylint: disable=invalid-name

    @classmethod
    def _generic_args_hook(cls, args: tuple) -> None:
        """Set matching logical resource class."""
        cls.matching_logical_cls = args[-1]

    def as_logical(self) -> LRG:
        """Return a logical resource that reflect this physical resource.

        Returns:
            LogicalCluster: A logical resource

        """
        resources = value_map(self, lambda r: r.as_logical())
        return self.matching_logical_cls(resources)

    # type error because mypy does not support generic typevars
    def __and__(self: PRG, other: PRG) -> PRG:  # type: ignore
        """Returns a intersection of two physical resources.

        Args:
            other (PhysicalCluster): The other physical resource

        Returns:
            PhysicalCluster: common physical resource

        """
        resource_dict: dict[K, P] = {}
        for index, node_resource in self.items():
            if index not in other:
                continue

            common = node_resource & other[index]
            if common:
                resource_dict[index] = common

        return self.__class__(resources=resource_dict)


class AllocationGroup(
    GenericArgsHookMixin, AbstractResourceGroup[K, A], Generic[K, A, G]
):
    """Group of allocations."""

    group_cls: ClassVar[Type[G]]  # pylint: disable=invalid-name

    @classmethod
    def _generic_args_hook(cls, args: tuple) -> None:
        """Set unit group class."""
        cls.group_cls = args[-1]

    @property
    def total(self) -> G:
        """Return total resource group."""
        return self.group_cls(value_map(self, lambda a: a.total))

    @property
    def acquired(self) -> G:
        """Return acquired resource group."""
        acquired = value_map(self, lambda a: a.acquired)
        return self.group_cls({k: v for k, v in acquired.items() if v})

    @property
    def released(self) -> G:
        """Return released resource group."""
        acquired = value_map(self, lambda a: a.released)
        return self.group_cls({k: v for k, v in acquired.items() if v})

    def acquire(self, group: G) -> AllocationGroup[K, A, G]:
        """Acquire a resource group.

        Raises:
            ValueError: if resource group cannot be acquired.

        """
        if not self.keys() >= group.keys():  # pylint: disable=no-member
            raise ValueError("Given group cannot be acquired")

        new_resources = dict(self)
        for idx, block in group.items():
            new_resources[idx] = new_resources[idx].acquire(block)
        return self.__class__(new_resources)

    def release(self, group: G) -> AllocationGroup[K, A, G]:
        """Release a resource group.

        Raises:
            ValueError: if resource group cannot be released.

        """
        if not self.keys() >= group.keys():  # pylint: disable=no-member
            raise ValueError("Given group cannot be released")

        new_resources = dict(self)
        for idx, block in group.items():
            new_resources[idx] = new_resources[idx].release(block)
        return self.__class__(new_resources)
