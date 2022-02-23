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

"""Crane cluster manger."""

# TODO: will be refactored in different PR.

from typing import List

from crane.common.model import dataclass, resource
from crane.core.common import db


class _Config:
    arbitrary_types_allowed = True


@dataclass(config=_Config)  # type: ignore  # pylint: disable=unexpected-keyword-arg
class JobState:
    """Job state.

    Args:
        queued (List[db.MiniCluster]): queued jobs
        running (List[db.MiniCluster]): running jobs

    """

    queued: List[db.MiniCluster]
    running: List[db.MiniCluster]


@dataclass
class ClusterState:
    """Current crane state.

    The SchedulePolicy component use this to generate actions.

    Args:
        job (JobState): state of current jobs
        resource (resource.PhysicalAllocationCluster): state of current resource

    """

    job: JobState
    resource: resource.PhysicalAllocationCluster
