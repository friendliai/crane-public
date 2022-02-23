# pylint: disable=unsubscriptable-object

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

"""Broadcaster and Subscriber."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Generic, TypeVar

T = TypeVar("T")


class QueueClosed(Exception):
    """Queue is already closed."""


class ClosableQueue(asyncio.Queue, Generic[T]):
    """Closable queue.

    Once the queue is closed, cannot be published.
    Does not inherit a queue, only implements the interface
    """

    # pylint: disable=W0231
    def __init__(self, maxsize: int = 0):
        """Initialize a queue."""
        self._q: asyncio.Queue[T | None] = asyncio.Queue(maxsize=maxsize)
        self._closed = False

    @property
    def closed(self):
        """Return True if queue is closed.

        Note that queue might be closed, but have some un-consumed items left.
        """
        return self._closed

    async def put(self, item: T):
        """Put an item into the queue.

        Args:
            item (T): Item to publish

        Raises:
            QueueClosed: if queue is already closed

        """
        if self._closed:
            raise QueueClosed("Queue is already closed")
        await self._q.put(item)

    def put_nowait(self, item: T):
        """Put an item into the queue (nonblocking).

        Args:
            item (T): Item to publish

        Raises:
            QueueClosed: if queue is already closed

        """
        if self._closed:
            raise QueueClosed("Queue is already closed")
        self._q.put_nowait(item)

    async def get(self) -> T | None:
        """Consume an item.

        Overrides return type

        Raises:
            QueueClosed: if queue will not produce any more items.

        """
        if self._q.empty() and self._closed:
            raise QueueClosed("Queue will not produce any more items.")
        return await self._q.get()

    def get_nowait(self) -> T | None:
        """Consume an item (nonblocking).

        Overrides return type

        Raises:
            QueueClosed: if queue will not produce any more items.

        """
        if self._q.empty() and self._closed:
            raise QueueClosed("Queue will not produce any more items.")
        return self._q.get_nowait()

    def close(self) -> None:
        """Close queue.

        The queue cannot be published anymore.
        """
        self._q.put_nowait(None)
        self._closed = True

    def __getattr__(self, name: str):
        """Delegate other attributes to queue."""
        return getattr(self._q, name)


class Channel(Generic[T]):
    """A channel that broadcasts all object of T to all subscriptions."""

    def __init__(self):
        """Initialize."""
        self.queues: list[ClosableQueue[T]] = []

    def broadcast(self, o: T) -> None:
        """Broadcasts an object of T to all subscriptions.

        Args:
            o (T): The object to broadcast
        """
        for queue in self.queues:
            queue.put_nowait(o)

    def subscribe(self) -> Subscription[T]:
        """Subscribes to this object.

        Returns:
            Subscription[T]: A subscription object

        """
        return Subscription(self)

    def close(self) -> None:
        """Close the channel and all subscriptions."""
        for queue in self.queues:
            queue.close()
        self.queues = []

    def is_empty(self) -> bool:
        """Returns True if channel has no subscriptions."""
        return not self.queues


class AsyncQueueIterator(AsyncIterator[T]):
    """An async iterator that goes over a queue.

    It stops when it gets None.
    """

    def __init__(self, queue: asyncio.Queue[T | None]) -> None:
        """Initialize."""
        self.queue = queue

    async def __anext__(self):
        """Iterate over the queue."""
        data = await self.queue.get()
        if data is None:
            raise StopAsyncIteration

        return data


class Subscription(Generic[T]):
    """A subscription that subscribes to a channel.

    This object is also an iterable.
    """

    def __init__(self, channel: Channel) -> None:
        """Initialize."""
        self.channel = channel
        self._queue: ClosableQueue[T] = ClosableQueue()
        self.channel.queues.append(self._queue)

    def close(self) -> None:
        """Close the subscription."""
        try:
            self.channel.queues.remove(self._queue)
        except ValueError:
            pass

    def __enter__(self) -> Subscription[T]:
        """Return itself.

        Returns:
            Subscription[T]:
        """
        return self

    def __aiter__(self) -> AsyncQueueIterator[T]:
        """Return an iterator over the events.

        Returns:
            AsyncQueueIterator[T]: An iterator

        """
        return AsyncQueueIterator(self._queue)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close the subscription."""
        self.close()

    def __del__(self) -> None:
        """Close this subscription."""
        self.close()
