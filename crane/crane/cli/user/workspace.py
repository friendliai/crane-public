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

"""Module dealing with workspace commands."""

from __future__ import annotations

import typer

from crane.cli.user.typing import UserClientContext

app = typer.Typer()


@app.command("init")
def workspace_init(ctx: UserClientContext):
    """Initialize current directory as Crane workspace."""
    client = ctx.obj

    if not client.ws.is_workspace_server_alive():
        typer.echo("Workspace server is not alive")
        return

    reinit_flag = client.ws.init()
    if reinit_flag:
        typer.echo("Reinitialized existing Crane workspace")
