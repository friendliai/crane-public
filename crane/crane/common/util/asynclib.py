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


"""Asyncio-related functions."""

from __future__ import annotations

import asyncio
from asyncio import FIRST_COMPLETED
from functools import wraps
from itertools import count
from typing import AsyncIterator, Awaitable, Callable, Iterable, Tuple, TypeVar

from crane.common.util.decorator import assert_python_version

T = TypeVar("T")
R = TypeVar("R")
TaskT = TypeVar("TaskT", bound=asyncio.Task)


async def aenumerate(iterable: AsyncIterator[T]) -> AsyncIterator[Tuple[int, T]]:
    """Enumerate, but for async iterators."""
    counter = count()
    async for item in iterable:
        yield next(counter), item


async def pipelined_async_map(
    func: Callable[[T], Awaitable[R]], iterable: Iterable[T], num_workers: int = 1
) -> AsyncIterator[R]:
    """Asynchronous map with a pipelined background task."""
    tasks = [asyncio.create_task(func(el)) for el in iterable]
    async for task in as_completed_in_order(tasks, num_workers):
        yield await task


async def as_completed_in_order(
    tasks: Iterable[TaskT], num_workers: int
) -> AsyncIterator[TaskT]:
    """Asynchronous iterator that iterates over tasks that are completed in order.

    low_watermark: the number of tasks yielded
    high_watermark: the number of tasks running or done

    """
    low_watermark, high_watermark = 0, num_workers
    tasks = list(tasks)
    task_in_order: dict[asyncio.Future, int] = {t: idx for idx, t in enumerate(tasks)}
    running_tasks: set[asyncio.Future] = set(tasks[low_watermark:high_watermark])
    done_task_indices: set[int] = set()

    while running_tasks:
        done, running_tasks = await asyncio.wait(
            running_tasks, return_when=FIRST_COMPLETED
        )

        for task in done:
            task_idx = task_in_order[task]
            done_task_indices.add(task_idx)

        if low_watermark in done_task_indices:
            for low_watermark in count(low_watermark):
                if low_watermark in done_task_indices:
                    done_task_indices.remove(low_watermark)
                    yield tasks[low_watermark]
                else:
                    break

            running_tasks.update(tasks[high_watermark : low_watermark + num_workers])
            high_watermark = low_watermark + num_workers

    assert not done_task_indices


# pylint: disable=protected-access
@assert_python_version("3.7+")
async def tick(sleep_wait_threshold: float = 0) -> None:
    """Block until all runnable coroutines have completed or suspended.

    Inspired from https://stackoverflow.com/questions/63732618

    This function only works for python native asyncio event loop, as it uses private
    attributes specific to asyncio.EventLoop. These attributes cannot be accessed
    publically. Use this function only for testing purposes.

    Note that if there is a timeout, this will block until the timeout expires.

    """
    double_checked = False
    loop = asyncio.get_running_loop()
    deadline = loop.time() + sleep_wait_threshold

    def _check():
        nonlocal double_checked, loop

        task_ready_queue = getattr(loop, "_ready")  # tasks that are ready to run
        task_schedules = getattr(loop, "_scheduled")  # asyncio.sleep

        if task_ready_queue:
            double_checked = False
            loop.call_soon(_check)
            return

        if not double_checked:
            # if one task sends a packet and another task receives it, the client task
            # could be suspended but can be woken up and read the packet.
            double_checked = True
            loop.call_soon(_check)
            return

        if task_schedules:
            # asyncio.sleep is dealt separately from ready queue.
            when = task_schedules[0].when()  # most recent task's schedule time
            if when < deadline:
                loop.call_at(when, _check)
                return

        event.set()  # no more task to proceed. Unblock event

    event = asyncio.Event()
    loop.call_soon(_check)  # start recursive check

    await event.wait()


async def periodic_timer(interval: float) -> AsyncIterator[None]:
    """An asynciterator that yields every `interval` seconds.

    Same as
        while True: await asyncio.sleep(interval)

    Temporarily disabled when `tick` is on.

    """
    while True:
        yield
        await asyncio.sleep(interval)


def sync_to_async(func: Callable) -> Callable:
    """Wrap synchronous function to run asynchronously with default executor."""

    @wraps(func)
    async def _wrapper(*args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args)

    return _wrapper
