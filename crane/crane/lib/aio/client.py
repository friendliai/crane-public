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

"""Crane lib types."""

from __future__ import annotations

import abc
import logging
from typing import Generic, TypeVar

from httpx import HTTPError

from crane.lib.common.config import FileBackedConfig
from crane.lib.common.exception import HTTPBadResponseError
from crane.lib.common.host import get_config_dir
from crane.vendor.http import AsyncHTTPClient


class ClientConfig(FileBackedConfig):
    """Base client configuration for crane app.

    All subclasses should override `url` default.
    """

    url: str = ""


C = TypeVar("C", bound=ClientConfig)
T = TypeVar("T", bound="AbstractCraneClient")

logger = logging.getLogger(__name__)


class AbstractCraneClient(abc.ABC, Generic[C]):
    """Abstract http protocol based client class."""

    app_name: str
    config_template: type[C]

    @classmethod
    def from_config(cls: type[T], config_path: str = "") -> T:
        """Create new client from local configuration file."""
        config_path = config_path or get_config_dir(cls.app_name)
        config = cls.config_template(config_path)

        # timeout for 10 minutes. A heuristic value
        # TODO: reduce timeout, and make admin socket streaming response.
        session = AsyncHTTPClient(config.url, timeout=60 * 10)
        return cls(session, config)

    def __init__(self, session: AsyncHTTPClient, config: C) -> None:
        """Initialize with http session."""
        self.session = session
        self.config = config

    @abc.abstractmethod
    async def ping(self) -> None:
        """Send ping request."""

    async def is_healthy(self) -> bool:
        """Return true if server responses with ping."""
        try:
            await self.ping()
            return True
        except (HTTPBadResponseError, HTTPError):
            return False

    async def close(self) -> None:
        """Close client."""
        await self.session.aclose()


class ClientCommandCollection(Generic[C]):
    """Collection of client subcommands."""

    def __init__(self, client: AbstractCraneClient[C]) -> None:
        """Initialize."""
        self.client = client

        # cache
        self._session = client.session
        self._config = client.config
