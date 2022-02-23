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

"""Mini cluster."""

from __future__ import annotations

from dataclasses import field
from typing import Optional, Sequence

from crane.common.model import dataclass, state
from crane.common.model.container import Config as ContainerConfig
from crane.common.model.resource import Logical, PhysicalCluster
from crane.common.util.serialization import DataClassJSONSerializeMixin


class State(state.State):
    """Mini cluster state.

    currently inactive:
        QUEUED: the mini cluster have not got any resource before

        RUNNING: the mini cluster is running
        PAUSED: the mini cluster have preempted full resource

        INVALID: invalid mini cluster configuration
        DONE: the mini cluster is finished gracefully.
        ERROR: the mini cluster has exited with an error

    """

    QUEUED = state.auto()

    RUNNING = state.auto()
    PAUSED = state.auto()

    ERROR = state.auto()
    INVALID = state.auto()
    DONE = state.auto()

    TERMINATED = INVALID | DONE | ERROR

    @staticmethod
    def __transitions__() -> list[tuple[State, State]]:
        """Return valid transitions."""
        # TODO: will sort out transition rules correctly at next PR.
        # TODO: add preempted state for RUNNING -> QUEUED.
        return [
            (State.QUEUED, State.RUNNING | State.ERROR),
            (State.RUNNING, State.QUEUED | State.PAUSED | State.TERMINATED),
            (State.PAUSED, State.RUNNING | State.ERROR),
        ]

    @staticmethod
    def __init_state__() -> State:
        """Mini clusters start from QUEUED state."""
        return State.QUEUED


@dataclass(frozen=True)
class StateHistory(state.StateHistory[State]):
    """Mini cluster state history."""

    states: Sequence[State]


@dataclass(init=False)
class ResourceSpec(DataClassJSONSerializeMixin):
    """Resource request option.

    Users specify locality here.
    If min resource is not specified, it is set to same as am_resource
    If max resource is not specified, it is set to same as min_resource

    Args:
        am_resource (Logical): app manager resource requirement
        min_resource (Optional[Logical]): minimum logical resource required.
        max_resource (Optional[Logical]): maximum logical resource wanted.

    """

    am_resource: Logical
    min_resource: Logical
    max_resource: Logical

    def __init__(
        self,
        am_resource: Logical,
        min_resource: Optional[Logical] = None,
        max_resource: Optional[Logical] = None,
    ) -> None:
        """Initialize."""
        self.am_resource = am_resource
        self.min_resource = am_resource if min_resource is None else min_resource
        self.max_resource = self.min_resource if max_resource is None else max_resource

        self.__post_init__()  # type: ignore  # pylint: disable=no-member

    def __post_init_post_parse__(self):
        """Validate by fastapi via pydantic."""
        if self.max_resource < self.min_resource:
            raise ValueError(
                f"Maximum resource({self.max_resource})"
                f" smaller than minimum resource({self.min_resource})."
            )

        if not self.am_resource <= self.min_resource:  # pylint: disable=unneeded-not
            raise ValueError(
                f"Minimum resource({self.min_resource}) should be greater than "
                f"app manager resource({self.am_resource})"
            )

        if not self.max_resource:
            raise ValueError(f"Maximum resource ({self.max_resource}) cannot be empty.")


@dataclass
class MiniClusterSetting(DataClassJSONSerializeMixin):
    """Settings for setting up mini cluster.

    Default mount: 1. user workspace, 2. common workspace (as readonly)

    Args:
        overlay (bool): whether to set overlay network. Defaults to True

    """

    overlay: bool = True


@dataclass
class Config(DataClassJSONSerializeMixin):
    """Job configuration.

    Args:
        app_manager (ContainerConfig): application manager configuration
        resource_spec (ResourceSpec): total resource spec
        mini_cluster_settting (MiniClusterSetting): mc setting. Has default config

    """

    app_manager: ContainerConfig
    resource_spec: ResourceSpec
    mini_cluster_setting: MiniClusterSetting = field(default_factory=MiniClusterSetting)


@dataclass
class Update(DataClassJSONSerializeMixin):
    """Job update configuration.

    Args:
        new_mini_cluster (PhysicalCluster): new mini cluster to claim.

    """

    new_mini_cluster: PhysicalCluster
