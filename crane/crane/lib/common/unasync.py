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

"""Unasync utilities.

Borrowed from github.com/python-trio/hip/src/ahip/util/unasync.py
"""

import asyncio
import inspect
import time

_original_next = next


def is_async_mode():
    """Tests if we're in the async part of the code or not."""

    async def f():
        """Unasync transforms async functions in sync functions."""
        return None

    obj = f()
    if obj is None:
        return False
    obj.close()  # prevent unawaited coroutine warning
    return True


ASYNC_MODE = is_async_mode()


async def anext(x):
    """Async version of next."""
    return await x.__anext__()


async def await_if_coro(x):
    """Async/sync compatible wrapper."""
    if inspect.iscoroutine(x):
        return await x
    return x


next = _original_next  # pylint: disable=redefined-builtin


def return_non_coro(x):
    """Sync mirror version of await_if_coro."""
    return x


async def async_sleep(t: float) -> None:
    """Sleep."""
    await asyncio.sleep(t)


def sync_sleep(t: float) -> None:
    """Sleep."""
    time.sleep(t)
