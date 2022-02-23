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

"""Crane user client.

A crane user must have:
    - crane gateway endpoint
    - crane user credentials

"""

from __future__ import annotations

import crane.common.constant as C
from crane.lib.aio.client import AbstractCraneClient
from crane.lib.aio.user.job import JobCommandCollection
from crane.lib.aio.user.mini_cluster import MiniClusterCommandCollection
from crane.lib.aio.user.resource import ResourceCommandCollection
from crane.lib.aio.user.typing import UserLibConfig
from crane.lib.aio.user.user import UserCommandCollection
from crane.lib.aio.user.workspace import WorkspaceCommandCollection
from crane.lib.common.http import assert_response
from crane.vendor.http import AsyncHTTPClient


class AsyncUserClient(AbstractCraneClient[UserLibConfig]):
    """Async client class for crane users.

    Attributes:
        job (JobCommandCollection): job commands
        mini_cluster (MiniClusterCommandCollection): Mini cluster commands
        resource (ResourceCommandCollection): Resource commands
        user (UserCommandCollection): User commands
        superuser (SuperuserCommandCollection): Superuser commands
        ws (WorkspaceCommandCollection): Workspace commands

    """

    app_name = "crane-user"
    config_template = UserLibConfig

    def __init__(self, session: AsyncHTTPClient, config: UserLibConfig) -> None:
        """Initialize."""
        super().__init__(session, config)

        # TODO: implement session that prefixes session
        self.mini_cluster = MiniClusterCommandCollection(self)
        self.resource = ResourceCommandCollection(self)
        self.user = UserCommandCollection(self)
        self.ws = WorkspaceCommandCollection(self)

        self.job = JobCommandCollection(self.mini_cluster)

        if self.config.access_token is not None:
            headers = dict(Authorization=f"Bearer {self.config.access_token}")
            self.session.headers.update(headers)

    async def ping(self) -> None:
        """Ping... and pong."""
        res = await self.session.get(f"/gateway{C.Gateway.URL.PING}", timeout=1)
        assert_response(res, 200)
