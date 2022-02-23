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

"""Basic resource constructs.

Logical: num_gpu (int)
Physical: gpu_indices (Set[int])

"""

from __future__ import annotations

from typing import FrozenSet, Iterable

from crane.common.model import dataclass
from crane.common.model.resource.typing import LogicalInterface, PhysicalInterface
from crane.common.util.serialization import DataClassJSONSerializeMixin


@dataclass(frozen=True, eq=False)
class Logical(LogicalInterface, DataClassJSONSerializeMixin):
    """Represent a resource of logical resource.

    It can be used for submitting a job, or request for launching cargo.

    Args:
        num_gpu (int): Number of of gpus

    """

    num_gpu: int

    def __post_init__(self) -> None:
        """Validate."""
        if self.num_gpu < 0:
            raise ValueError("'num_gpu' must be non-negative integer.")

    @classmethod
    def empty(cls) -> Logical:
        """Empty logical resource unit."""
        return cls(num_gpu=0)

    def __add__(self, other: Logical) -> Logical:
        """Add two physical resources."""
        if not isinstance(other, Logical):
            return NotImplemented

        new_num_gpu = self.num_gpu + other.num_gpu
        return Logical(new_num_gpu)

    def __sub__(self, other: Logical) -> Logical:
        """Subtract two physical resources."""
        if not isinstance(other, Logical):
            return NotImplemented

        new_num_gpu = self.num_gpu - other.num_gpu
        if new_num_gpu < 0:
            raise ValueError("GPU count cannot be negative.")

        return Logical(new_num_gpu)

    def __bool__(self) -> bool:
        """Return True if the resource is empty."""
        return self.num_gpu != 0

    # note that without __lt__, __eq__, dataclass raises error even with order=True
    def __lt__(self, other: Logical) -> bool:
        """Check self is less than other."""
        if not isinstance(other, Logical):
            return NotImplemented

        return self.num_gpu < other.num_gpu

    def __gt__(self, other: Logical) -> bool:
        """Check self is greater than other."""
        if not isinstance(other, Logical):
            return NotImplemented

        return self.num_gpu > other.num_gpu

    def __eq__(self, other: object) -> bool:
        """Check if one contains another."""
        if not isinstance(other, Logical):
            return NotImplemented

        return self.num_gpu == other.num_gpu


@dataclass(frozen=True, eq=False, init=False)
class Physical(PhysicalInterface[Logical], DataClassJSONSerializeMixin):
    """Represent a unit of physical resource.

    Args:
        gpu_indices (Iterable[int]): GPU indices

    """

    gpu_indices: FrozenSet[int]

    def __init__(self, gpu_indices: Iterable[int]) -> None:
        """Initialize."""
        object.__setattr__(self, "gpu_indices", frozenset(gpu_indices))

    @classmethod
    def empty(cls) -> Physical:
        """Empty physical resource unit."""
        return cls(gpu_indices=frozenset())

    def as_logical(self) -> Logical:
        """Return a logical resource that reflect this physical resource.

        Returns:
            Logical: A logical resource

        """
        num_gpu = len(self.gpu_indices)
        return Logical(num_gpu)

    def is_subset(self, other: Physical) -> bool:
        """Return true if the given resource is a subset of this group."""
        return self <= other

    def __add__(self, other: Physical) -> Physical:
        """Add two physical resources."""
        if not isinstance(other, Physical):
            return NotImplemented

        if self.gpu_indices.intersection(other.gpu_indices):
            raise ValueError("Two physical resources have the same GPU")

        new_gpu_indices = self.gpu_indices.union(other.gpu_indices)
        return Physical(new_gpu_indices)

    def __sub__(self, other: Physical) -> Physical:
        """Subtract two physical resources."""
        if not isinstance(other, Physical):
            return NotImplemented

        if not self.gpu_indices.issuperset(other.gpu_indices):
            raise ValueError("Invalid gpu_indices.")

        new_gpu_indices = self.gpu_indices.difference(other.gpu_indices)
        return Physical(new_gpu_indices)

    def __bool__(self) -> bool:
        """Return True if the resource is empty."""
        return bool(self.gpu_indices)

    def __lt__(self, other: Physical) -> bool:
        """Returns if a physical resource is subset of this."""
        if not isinstance(other, Physical):
            return NotImplemented

        return self.gpu_indices < other.gpu_indices

    def __gt__(self, other: Physical) -> bool:
        """Returns if a physical resource is superset of this."""
        if not isinstance(other, Physical):
            return NotImplemented

        return self.gpu_indices > other.gpu_indices

    def __eq__(self, other: object) -> bool:
        """Returns if a physical resource is subset of this."""
        if not isinstance(other, Physical):
            return NotImplemented

        return self.gpu_indices == other.gpu_indices

    def __and__(self, other: Physical) -> Physical:
        """Returns a intersection of two physical resources.

        Args:
            other (Physical): The other physical resource

        Returns:
            Physical: common physical resource

        """
        new_gpu_indices = self.gpu_indices.intersection(other.gpu_indices)
        return Physical(gpu_indices=new_gpu_indices)
