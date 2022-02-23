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

"""Resource Groups."""

from __future__ import annotations

from typing import Mapping

from crane.common.model import dataclass
from crane.common.model.resource.allocation import LogicalAllocation, PhysicalAllocation
from crane.common.model.resource.group import LogicalCluster, PhysicalCluster
from crane.common.model.resource.typing import (
    AbstractLogicalResourceGroup,
    AbstractPhysicalResourceGroup,
    AllocationGroup,
)
from crane.common.util.serialization import DataClassJSONSerializeMixin


@dataclass(eq=False, init=False, order=False)
class LogicalAllocationCluster(
    AbstractLogicalResourceGroup[str, LogicalAllocation],
    AllocationGroup[str, LogicalAllocation, LogicalCluster],
    DataClassJSONSerializeMixin,
):
    """A group of logical allocated resources."""

    resources: Mapping[str, LogicalAllocation]


@dataclass(eq=False, init=False, order=False)
class PhysicalAllocationCluster(
    AbstractPhysicalResourceGroup[str, PhysicalAllocation, LogicalAllocationCluster],
    AllocationGroup[str, PhysicalAllocation, PhysicalCluster],
    DataClassJSONSerializeMixin,
):
    """A group of physical allocated resources."""

    resources: Mapping[str, PhysicalAllocation]
