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

"""Util for crane_cli display."""

from __future__ import annotations

import datetime
import os
from typing import NoReturn

import typer
from dateutil.parser import parse

import crane.common.constant as C


def build_time_delta(prev_time: str | datetime.datetime) -> str:
    """Create a coarse time delta between now and the given point of time.

    Args:
        prev_time (str | datetime.datetime): datetime string

    Returns:
        A coarse string representation of time delta

    """
    if isinstance(prev_time, str):
        prev_time = parse(prev_time)

    current_time = datetime.datetime.utcnow()
    time_elapsed = current_time - prev_time

    year = time_elapsed.days // 365
    hour = time_elapsed.seconds // 3600
    minute = time_elapsed.seconds // 60

    if year > 0:
        time = f"{year}y"
    elif time_elapsed.days > 0:
        time = f"{time_elapsed.days}d"
    elif hour > 0:
        time = f"{hour}h"
    elif minute > 0:
        time = f"{minute}m"
    else:
        time = f"{time_elapsed.seconds}s"

    return time


def error(err_msg: str, exit_code: int = 1) -> NoReturn:
    """Print error message and exit program."""
    typer.secho(err_msg, fg=typer.colors.MAGENTA, err=True)
    raise typer.Exit(exit_code)


def warn(warn_msg: str) -> None:
    """Print warning message.

    Does not print warning if suppressed
    """
    if C.CLIEnv.IGNORE_WARNING in os.environ:
        return
    typer.secho(warn_msg, fg=typer.colors.YELLOW)


def info(info_msg: str) -> None:
    """Print info message."""
    typer.echo(info_msg)
