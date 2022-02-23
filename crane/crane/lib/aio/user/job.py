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

"""Job subcommands for crane user client."""

from __future__ import annotations

from typing import AsyncIterator

from crane.common.api_model import MCCreateResponse, MCInspectResponse
from crane.common.model import log as log_model
from crane.lib.aio.user.mini_cluster import MiniClusterCommandCollection


class JobCommandCollection:
    """Job subcommands."""

    def __init__(self, mini_cluster: MiniClusterCommandCollection) -> None:
        """Initialize."""
        self.mini_cluster = mini_cluster

    async def filter(
        self,
        job_id_or_name: str,
        tags: list[str] | None = None,
        state: list[str] | None = None,
    ) -> list[str]:
        """Filter jobs by id, name or tags."""
        return await self.mini_cluster.filter(job_id_or_name, tags, state)

    async def inspect(self, job_id: str) -> MCInspectResponse:
        """Inspect a job by its id."""
        return await self.mini_cluster.inspect(job_id)

    async def kill(self, job_id: str, force: bool) -> None:
        """Kill a job by its id."""
        return await self.mini_cluster.kill(job_id, force)

    async def delete(self, job_id: str) -> None:
        """Remove a job by its id."""
        return await self.mini_cluster.delete(job_id)

    # pylint: disable=too-many-arguments
    async def add(self, *args, **kwargs) -> MCCreateResponse:
        """Add a new job to cluster."""
        # TODO: args will be added later. Removed now to avoid lint error
        return await self.mini_cluster.add(*args, **kwargs)

    async def log(
        self,
        job_id: str,
        follow: bool = False,
        filter_: log_model.LogFilter = log_model.LogFilter(),
    ) -> AsyncIterator[log_model.Log]:
        """Iterate through a log."""
        async for log in self.mini_cluster.log(job_id, follow, filter_):
            yield log
