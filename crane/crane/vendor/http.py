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

"""Http client implementations."""

from __future__ import annotations

from collections import ChainMap
from typing import Any

from httpcore import AsyncConnectionPool, SyncConnectionPool
from httpx import URL, AsyncClient, Client, Headers, Request, create_ssl_context
from httpx._utils import same_origin


class HTTPxUDSMixin:
    """Creates new http sessions.

    Args:
        endpoint (str): http endpoint

    """

    UNIX_DOMAIN_SOCKET_PREFIX = "uds://"

    def _get_init_args(
        self, endpoint: str, pool_cls: type[SyncConnectionPool | AsyncConnectionPool]
    ) -> dict[str, Any]:
        """Initialize."""
        if endpoint.startswith(self.UNIX_DOMAIN_SOCKET_PREFIX):
            endpoint = endpoint[len(self.UNIX_DOMAIN_SOCKET_PREFIX) :]

            # wait until httpx v1.0 kicks in.
            # uds is supported by httpcore not httpx until then.
            transport = pool_cls(
                ssl_context=create_ssl_context(),
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=5.0,
                uds=endpoint,
                retries=5,
            )
            base_url = "http://localhost"
            # TODO: handle path in base_url
            return dict(transport=transport, base_url=base_url)

        return dict(base_url=endpoint)

    # WARNING !!!
    #   We do not remove Authorization header upon redirect. This is not safe.
    #   This should be removed in the future.
    # pylint: disable=no-self-use
    def _redirect_headers(self, request: Request, url: URL, method: str) -> Headers:
        headers = Headers(request.headers)

        if not same_origin(url, request.url):
            headers.pop("Host", None)

        if method != request.method and method == "GET":
            headers.pop("Content-Length", None)
            headers.pop("Transfer-Encoding", None)

        headers.pop("Cookie", None)

        return headers


class SyncHTTPClient(HTTPxUDSMixin, Client):
    """Synchronous http client."""

    def __init__(self, endpoint: str, *args, **kwargs) -> None:
        """Initialize."""
        default_kwargs = self._get_init_args(endpoint, SyncConnectionPool)
        super().__init__(*args, **ChainMap(default_kwargs, kwargs))


class AsyncHTTPClient(HTTPxUDSMixin, AsyncClient):
    """Asynchronous http client."""

    def __init__(self, endpoint: str, *args, **kwargs) -> None:
        """Initialize."""
        default_kwargs = self._get_init_args(endpoint, AsyncConnectionPool)
        super().__init__(*args, **ChainMap(default_kwargs, kwargs))
