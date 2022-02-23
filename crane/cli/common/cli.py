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

"""Crane CLI typer-related utilities."""

from functools import wraps
from typing import Callable

import typer

from crane.cli.common.context import TyperContext
from crane.cli.common.display import error
from crane.lib.sync.client import AbstractCraneClient


# todo: add type hints
def ignore_completion(callback):
    """Decorator that makes callbacks ignore calls from autocompletion.

    Though counter-intuitive, callback functions are invoked during
    autocompletion. Thus, callback functions must ignore such calls
    by looking at the current typer context.
    """
    # return callback

    def _callback(ctx: typer.Context, value):
        if ctx.resilient_parsing:
            return None
        return callback(value)

    return _callback


def check_connection(f: Callable) -> Callable:
    """Decorator that checks connection to server."""

    @wraps(f)
    def _check(**kwargs):
        ctx: TyperContext[AbstractCraneClient] = kwargs["ctx"]
        client = ctx.obj
        if not client.is_healthy():
            error("Connection to server failed.\nTry changing the cli configuration.")
        return f(**kwargs)

    return _check
