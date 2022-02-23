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

"""Resource definition of crane.

Logical: num_gpu (int)
Physical: gpu_indices (Set[int])

"""

from __future__ import annotations

from crane.common.model import dataclass
from crane.common.model.resource.base import Logical, Physical
from crane.common.model.resource.typing import (
    AbstractAllocation,
    LogicalInterface,
    PhysicalInterface,
)
from crane.common.util.serialization import DataClassJSONSerializeMixin


@dataclass(frozen=True)
class LogicalAllocation(
    AbstractAllocation[Logical], LogicalInterface, DataClassJSONSerializeMixin
):
    """Allocation object of logical resources."""

    total: Logical
    released: Logical

    @classmethod
    def empty(cls) -> LogicalAllocation:
        """Return a empty resource."""
        return LogicalAllocation(Logical.empty(), Logical.empty())


@dataclass(frozen=True)
class PhysicalAllocation(
    AbstractAllocation[Physical],
    PhysicalInterface[LogicalAllocation],
    DataClassJSONSerializeMixin,
):
    """Allocation object of physical resources."""

    total: Physical
    released: Physical

    @classmethod
    def empty(cls) -> PhysicalAllocation:
        """Return a empty resource."""
        return PhysicalAllocation(Physical.empty(), Physical.empty())

    def as_logical(self) -> LogicalAllocation:
        """Return a logical allocation resource."""
        # pylint: disable=abstract-class-instantiated
        return LogicalAllocation(self.total.as_logical(), self.released.as_logical())

    def __and__(self, other: PhysicalAllocation) -> PhysicalAllocation:
        """Return an intersection with another allocation."""
        return PhysicalAllocation(
            self.total & other.total, self.released & other.released
        )
