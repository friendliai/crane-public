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

"""Crane user related commands."""

import typer

import crane.common.constant as C
from crane.cli.common.cli import check_connection
from crane.cli.common.display import error, info
from crane.cli.user.typing import UserClientContext
from crane.lib.common.exception import HTTPBadResponseError

app = typer.Typer()


@app.command("signin")
@check_connection
def sign_in(
    ctx: UserClientContext,
    web: bool = typer.Option(
        True, "--web/--no-web", help="Whether to automatically open a web browser."
    ),
):
    """Sign in to crane."""
    client = ctx.obj
    try:
        client.user.sign_in(web)
    except OSError:
        error("Failed to open web browser.\nTry `crane user signin --no-web")

    info(C.Template.SIGN_IN_SUCCESS)


@app.command("signout")
@check_connection
def sign_out(ctx: UserClientContext):
    """Sign out of crane."""
    client = ctx.obj
    ans = typer.prompt("Are you sure you want to log out? (Y/n)", "y")
    if ans != "y":
        error("Failed to log out")
    client.user.sign_out()
    info(C.Template.SIGN_OUT_SUCCESS)


@app.command("whoami")
@check_connection
def whoami(ctx: UserClientContext):
    """See current logged in user information."""
    client = ctx.obj

    try:
        user_info = client.user.whoami()
    except HTTPBadResponseError as e:
        error(str(e))

    info_str = "id: {info.id}\nusername: {info.username}".format(info=user_info)
    if user_info.is_superuser:
        info_str += typer.style("\t[ADMIN]", fg=typer.colors.BRIGHT_RED)
    info(str(info_str))
