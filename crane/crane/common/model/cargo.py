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


"""Cargo table.

Each cargo belongs to a mini cluster.
# TODO: will be removed totally
"""

from __future__ import annotations

from typing import List, Optional

from crane.common.model import container, dataclass, resource
from crane.common.util.serialization import DataClassJSONSerializeMixin


@dataclass
class Cargo(DataClassJSONSerializeMixin):
    """Cargo definition.

    Args:
        name (str): name of the cargo
        containers (List[container.Container]): containers
        manager (bool): If this cargo is a AM

    """

    name: str
    containers: List[container.Container]
    manager: bool

    def __post_init__(self) -> None:
        """Validate."""
        if not self.containers:
            raise ValueError("Cargo cannot be empty.")


@dataclass
class CargoContainerRequest(DataClassJSONSerializeMixin):
    """Container request for cargos.

    each container is assigned physical resource, and node.

    Args:
        config (container.Config): container configuration
        resource (container.Allocation): container.resource

    """

    config: container.Config
    resource: container.Allocation


@dataclass
class Request(DataClassJSONSerializeMixin):
    """Cargo Request definition.

    If name is empty, it will be assigned by crane.

    Args:
        name (Optional[str]): name of the cargo
        containers (List[CargoContainerRequest]): container requests

    """

    name: Optional[str]
    containers: List[CargoContainerRequest]

    def total_resource(self) -> resource.PhysicalCluster:
        """Return total resource requested by this cargo.

        Returns:
            resource.PhysicalCluster: Physical resource group this cargo requests.

        """
        resources: List[resource.PhysicalCluster] = [
            container.resource.to_physical_cluster() for container in self.containers
        ]
        return resource.PhysicalCluster.sum(*resources)


@dataclass
class Update(DataClassJSONSerializeMixin):
    """Cargo update configuration.

    Args:
        removals (List[str]): list of container names to remove
        additions (List[CargoContainerRequest]): list of container requests

    """

    removals: List[str]
    additions: List[CargoContainerRequest]
