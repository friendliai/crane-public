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

"""Crane user client user commands."""

from __future__ import annotations

import logging
import webbrowser

from rich.console import Console

import crane.common.constant as C
from crane.common.api_model import user
from crane.common.util.sequence import generate_sequence
from crane.lib.aio.client import ClientCommandCollection
from crane.lib.aio.user.typing import UserLibConfig
from crane.lib.common.http import assert_response
from crane.lib.common.unasync import async_sleep

logger = logging.getLogger(__name__)


class UserCommandCollection(ClientCommandCollection[UserLibConfig]):
    """Commands for session management."""

    async def sign_in(self, browser: bool = True) -> None:
        """Sign in to crane.

        # TODO: add other authorization strategies for scripts
        # TODO: move console prints to cli level.

        Args:
            browser (bool): If true, opens the browser. Defaults to True.

        """
        # initiate device login flow.
        res = await self._session.get(f"/gateway{C.Gateway.URL.AUTH_DEVICE}")
        assert_response(res)
        flow_info = user.DeviceFlowInfo.from_json(res.text)

        if browser:
            input("Press ENTER to open login page in your browser.")
            has_browser = webbrowser.open(flow_info.redirect_uri)
            if not has_browser:
                # TODO: need better exception class.
                raise OSError("No web browser found.")

        else:
            print("Go to the link below in a web browser.", flush=True)
            print(flow_info.redirect_uri, flush=True)

        # wait until login is completed

        console = Console()
        body = user.TokenRequest(device_code=flow_info.device_code)

        with console.status(
            "[bold green]Checking for authorization results...", spinner="pong"
        ):
            for sleep_duration in generate_sequence("fibonacci", init=2, upper=10):
                await async_sleep(sleep_duration)
                res = await self._session.post(
                    f"/gateway{C.Gateway.URL.AUTH_DEVICE_TOKEN}", json=body.to_dict()
                )
                assert_response(res, (200, 429))

                if res.status_code == 200:
                    break

        token = user.Token.from_json(res.text)
        self._config.access_token = token.access_token
        self._config.refresh_token = token.refresh_token
        self._config.save()

    async def sign_out(self) -> None:
        """Sign out user.

        Raises:
            HTTPBadResponseError: if status code is not expected
            ConnectError: if connection fails

        """
        self._config.access_token = None
        self._config.refresh_token = None
        self._config.save()

    async def whoami(self) -> user.UserInfo:
        """Return public user info about this user.

        Returns:
            user.UserInfo: user info

        Raises:
            HTTPBadResponseError: if status code is not expected
            ConnectError: if connection fails

        """
        res = await self._session.get(f"/gateway{C.Gateway.URL.USER_DETAIL}")
        assert_response(res)
        return user.UserInfo.from_json(res.text)
