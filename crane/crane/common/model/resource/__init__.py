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

"""Resource definition of crane."""

from crane.common.model.resource.allocation import LogicalAllocation, PhysicalAllocation
from crane.common.model.resource.allocation_group import (
    LogicalAllocationCluster,
    PhysicalAllocationCluster,
)
from crane.common.model.resource.base import Logical, Physical
from crane.common.model.resource.group import LogicalCluster, PhysicalCluster

__all__ = [
    "Logical",
    "Physical",
    "LogicalAllocation",
    "LogicalAllocationCluster",
    "PhysicalAllocation",
    "LogicalCluster",
    "PhysicalCluster",
    "PhysicalAllocationCluster",
]
