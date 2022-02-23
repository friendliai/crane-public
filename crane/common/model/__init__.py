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

"""Crane models.

User: each user needs to be registered in the db.

GPU: A logical abstraction of a gpu:
    each gpu has its own row.
    #TODO: later extend to "processor" concept

Node: A node is logical abstraction of endpoint and resources (GPU)

Container: Abstraction of a running process.
    A container belongs to a node, and a cargo.
    It also has set of resources (GPU).

    options:
    - image: program dependency
    - process: command, environment variables
    - file: file system mount
    - network: port opening from container to host, network between containers
    - resource: cpu, memory, gpu
    - runtime: other docker runtime related

Cargo: A set of containers.
    It is a logical abstraction of group of containers working together.
    E.g. Distributed training.
    Each cargo belongs to one mini cluster.
    This is the scheduling unit.
    Note that a cargo can go over a single node boundary.

MiniCluster: Set of resources permitted to an app.
    It is sent to each job upon running.
    Note that each mini cluster can be varied.
    For example, a mini cluster may request more resources.

Job: Job abstraction.
    When a user submits a job to Crane, Crane executes the job in the form of an app.
    That is, an app is a job in execution.
    Each job has user key, and resource limit.


"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from pydantic.dataclasses import dataclass

__all__ = ["dataclass"]
