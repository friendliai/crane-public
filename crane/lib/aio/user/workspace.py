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

"""Crane user client workspace commands."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

import crane.common.constant as C
from crane.lib.aio.client import ClientCommandCollection
from crane.lib.aio.user.typing import UserLibConfig
from crane.lib.aio.user.ws import zip_workspace
from crane.lib.common.http import assert_response


class WorkspaceCommandCollection(ClientCommandCollection[UserLibConfig]):
    """Commands for workspaces."""

    # pylint: disable=no-self-use
    async def init(self) -> bool:
        """Initialize crane workspace in git-like manner.

        After init function, the directory will look like,
        /
        |_ .crane/
            |_ config.yaml
            |_ .craneignore
            |_ {workspace_id}.tar

        Returns:
            bool: whether re-initialize

        """
        context_path = Path.cwd() / C.Workspace.CONTEXT_DIR
        config_path = context_path / C.Workspace.CONFIG_PATH

        reinit_flag = config_path.exists()

        if not reinit_flag:
            os.makedirs(context_path, exist_ok=True)

            default_config = {"container_path": _default_container_path()}
            with open(config_path, "w", encoding="utf-8") as f:
                # TODO: implement more on config file
                yaml.dump(default_config, f)

        return reinit_flag

    # pylint: disable=no-self-use
    async def add(self) -> str:
        """Zip workspace and send the tarball to server.

        Returns:
            context_id (str): id of newly created context

        """
        zip_file_path = zip_workspace(Path.cwd())
        with open(zip_file_path, "rb") as f:
            files = {"file": ("file", f, "application/x-tar")}
            res = await self._session.post(
                f"/workspace{C.WsServer.URL.WORKSPACE}", files=files
            )

        assert_response(res, 201)
        context_id = res.json()

        # TODO: remove zip_file_path

        return context_id

    async def is_workspace_server_alive(self) -> bool:
        """Check if ws server is alive."""
        res = await self._session.get(f"/workspace{C.WsServer.URL.PING}", timeout=1)
        return res.status_code == 200


def _default_container_path() -> str:
    """Default container path is specified as current directory."""
    return os.getcwd()
