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

"""Crane CLI configuration related commands."""

from __future__ import annotations

import json
import platform
import pprint
import sys
from pathlib import Path

import typer

from crane import __version__ as crane_v
from crane.cli.common.context import TyperContext
from crane.cli.common.display import error, info
from crane.lib.sync.client import AbstractCraneClient, ClientConfig

USING_LOCAL_CRANE_WARNING = """\
crane-cli will send requests to locally running crane.\
"""


class GenericTyperContext(TyperContext[AbstractCraneClient[ClientConfig]]):
    """Generic typer context for crane apps."""


def _print_version(print_version: bool) -> None:
    """A Callback function that implements CLI option '--version'.

    Args:
        print_version (bool): This sets to be True when option '--version' gets passed.

    """
    checkpoint_file = "checkpoint.json"
    checkpoint_path = Path(__file__).absolute().parent.parent.parent / checkpoint_file

    if not print_version:
        return

    try:
        with checkpoint_path.open() as f:
            git_checkpoint = json.load(f)
            git_info = (
                "Git branch:\t\t{ckpt[git_branch]}\n"
                + "Git commit:\t\t{ckpt[git_commit]}\n"
                + "Git timestamp:\t\t{ckpt[git_timestamp]}"
            ).format(ckpt=git_checkpoint)
    except OSError:
        git_info = "Git info:\t\tNot Available"

    version_info = "Python version:\t\t{v.major}.{v.minor}.{v.micro}".format(
        v=sys.version_info
    )
    architecture = platform.processor() or "Not Available"

    info(
        "\n".join(
            [
                f"Version:\t\t{crane_v}",
                version_info,
                git_info,
                f"OS/Arch:\t\t{platform.system()}/{architecture}",
            ]
        )
    )

    raise typer.Exit(code=0)


def add_config_commands(app: typer.Typer, client_cls: type[AbstractCraneClient]):
    """Change url type and path.

    Args:
        app (typer.Typer): typer application
        client_cls (type[AbstractCraneClient]): Client class

    """
    # define callback

    # pylint: disable=unused-variable
    @app.callback()
    def _global_commands(
        ctx: GenericTyperContext,
        _: bool = typer.Option(
            False,
            "--version",
            "-V",
            help="Print Crane CLI version",
            callback=_print_version,
            is_eager=True,
        ),
    ) -> None:
        nonlocal client_cls
        ctx.obj = client_cls.from_config()

    config_sub_app = typer.Typer()

    # pylint: disable=unused-variable
    @config_sub_app.command("set")
    def set_config(ctx: GenericTyperContext, value: str) -> None:
        """Set new configuration.

        Right now, only url can be configured.
        """
        if not value.startswith("url="):
            error("Not implemented. Only url configuration is supported.")

        value = value[len("url=") :]

        if not value.startswith(("http", "uds")):
            error("Invalid url. should start with http:// or uds://")

        ctx.obj.config.url = value
        ctx.obj.config.save()

    # pylint: disable=unused-variable
    @config_sub_app.command("list")
    def list_config(ctx: GenericTyperContext) -> None:
        """Get current crane url."""
        cli_ctx = ctx.obj
        info(pprint.pformat(cli_ctx.config.to_dict()))

    app.add_typer(
        config_sub_app,
        name="config",
        help="Configuration related commands.",
    )
