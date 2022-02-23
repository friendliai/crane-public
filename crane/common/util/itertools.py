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

"""Utilities for iterating."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from functools import wraps
from typing import AsyncIterable, Callable, Iterable, Mapping, TypeVar

from crane.common.util.channel import AsyncQueueIterator, ClosableQueue

T = TypeVar("T")


def bigram(items: Iterable[T]) -> Iterable[tuple[T, T]]:
    """Iterate list by bigram pair.

    Args:
        items (Iterable[T]): list to iterate

    Returns:
        Iterable[tuple[T, T]]: Bigram

    """
    prev: T | None = None
    for curr in items:
        if prev is not None:
            yield prev, curr
        prev = curr


def first(items: Iterable[T]) -> T | None:
    """Return the first element of a list. Returns None if the list is empty.

    Args:
        items (Iterable[T]): iterable to fetch item from

    Returns:
        T | None: None or first element of the list

    """
    for i in items:
        return i
    return None


def split(iter_: Iterable[T], func: Callable[[T], bool]) -> tuple[list[T], list[T]]:
    """Partition an iterable into two iterables with a given function.

    Args:
        iter_ (Iterable[T]): an iterable to split
        func (Callable[[T], bool]): function to evaluate the items

    Returns:
        tuple[list[T], list[T]]: pair of list each with truthy and falsy items.

    """
    splits: dict[bool, list[T]] = {True: [], False: []}
    for o in iter_:
        splits[func(o)].append(o)
    return splits[True], splits[False]


K = TypeVar("K")
V = TypeVar("V")
V_ = TypeVar("V_")


def value_map(mapping: Mapping[K, V], func: Callable[[V], V_]) -> Mapping[K, V_]:
    """Map dictionary values."""
    return {k: func(v) for k, v in mapping.items()}


def adebounce(interval: float):
    """Asynchronous debounce function decorator."""

    def _decorator(func):
        fut: asyncio.TimerHandle | None = None

        @wraps(func)
        def wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()

            async def call_it():
                await func(*args, **kwargs)

            nonlocal fut
            if fut is not None:
                fut.cancel()

            fut = loop.call_later(interval, call_it)

        return wrapper

    return _decorator


async def adebounce_iter(
    aiter: AsyncIterable[T], interval: float = 1.0
) -> AsyncIterable[T]:
    """Debounce un-consumed items in queue."""
    queue: ClosableQueue[T] = ClosableQueue()

    @adebounce(interval)
    async def _put(item: T) -> None:
        queue.put(item)

    async def _subscribe() -> None:
        async for item in aiter:
            await _put(item)
        queue.close()

    bg_task = asyncio.create_task(_subscribe())

    try:
        async for item in AsyncQueueIterator(queue):
            yield item
    except asyncio.CancelledError:
        bg_task.cancel()
        raise
    finally:
        with suppress(asyncio.CancelledError):
            await bg_task
