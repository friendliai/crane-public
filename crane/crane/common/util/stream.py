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

"""Stream utilities.

A stream is a asynchronous iterator.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, TypeVar

T = TypeVar("T")


def anext_task(stream: AsyncIterator[T]) -> asyncio.Task[T]:
    """Return a task that returns next element of async stream."""
    return asyncio.create_task(stream.__anext__())


async def merge(*streams: AsyncIterator[T]) -> AsyncIterator[T]:
    """Merge multiple streams into one stream(iterator)."""
    stream_list = list(streams)
    tasks: "list[asyncio.Future[T]]" = [anext_task(s) for s in stream_list]

    while tasks:
        assert len(tasks) == len(stream_list)
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # read from done
        for task in done:
            try:
                yield await task
            except StopAsyncIteration:
                idx = tasks.index(task)
                del tasks[idx]
                del stream_list[idx]

        # re-read stream
        # use range(len) instead of enumerate to avoid copying
        for idx in range(len(tasks)):  # pylint: disable=consider-using-enumerate
            if tasks[idx] in done:
                tasks[idx] = anext_task(stream_list[idx])
