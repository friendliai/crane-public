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

"""Job router models."""

from __future__ import annotations

from dataclasses import field
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from crane.common.model import dataclass, mini_cluster
from crane.common.model.resource import PhysicalCluster
from crane.common.util.serialization import (
    DataClassJSONSerializeMixin,
    DataClassYAMLMixin,
)


@dataclass
class MCCreateResponse(DataClassJSONSerializeMixin):
    """Mini cluster create response.

    Args:
        mc_id (str): mini cluster ID
        name (str): mini cluster name
        add_time (float): creation timestamp

    """

    mc_id: str
    name: str
    add_time: float


@dataclass
class MCStates(DataClassJSONSerializeMixin):
    """Mini cluster state history.

    Args:
        states (list): a list of state history

    """

    states: List[Tuple[str, datetime]]

    @classmethod
    def from_state_history(cls, state_history: mini_cluster.StateHistory) -> MCStates:
        """Create MCStates from state history."""
        return MCStates(
            [
                (state.name, datetime.utcfromtimestamp(time))
                for state, time in state_history
            ]
        )

    @property
    def curr(self) -> str:
        """Get the current state."""
        return self.states[-1][0]

    @property
    def timestamp(self) -> datetime:
        """Get the latest transition timestamp."""
        return self.states[-1][1]

    @property
    def created(self) -> datetime:
        """Get the creation timestamp."""
        return self.states[0][1]


@dataclass
class MCInspectResponse(DataClassJSONSerializeMixin, DataClassYAMLMixin):
    """Job status.

    Args:
        user_id (str): user that owns the job
        job_id (UUID): job identifier
        name (Optional[str]): job name
        tags (List[str]): job tags
        job_config (Config): job configuration
        state_history (MCStates): job state history
        acquired_resource (PhysicalCluster): resource allocated to this job

    """

    user_id: str
    job_id: UUID
    name: str
    tags: List[str]
    job_config: mini_cluster.Config
    state_history: MCStates
    acquired_resource: PhysicalCluster


@dataclass
class MCCreateRequest(DataClassJSONSerializeMixin):
    """Job request.

    Args:
        config (Config): job configuration
        name (str): job name
        workspace_id (str) : workspace id if needed
        tags (List[str]): list of job tags

    """

    config: mini_cluster.Config
    name: Optional[str]
    workspace_id: Optional[str]
    tags: List[str] = field(default_factory=list)
