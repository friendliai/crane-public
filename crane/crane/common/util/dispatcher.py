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

"""Utilities for dispatching events.

Unlike channel, dispatchers is used for routing events to designated callers.
"""

from contextlib import suppress
from typing import Generic, TypeVar

from crane.common.util.channel import Channel, Subscription

K = TypeVar("K")
T = TypeVar("T")


class Dispatcher(Generic[K, T]):
    """A dispatcher has several channels by key, and one general channel."""

    def __init__(self):
        """Initialize dispatcher."""
        self.channels: dict[K, Channel[T]] = {}
        self.general: Channel[T] = Channel()

    def dispatch(self, key: K, o: T) -> None:
        """Dispatches an object o to channels with key {key}.

        Args:
            key (K): key of object
            o (T): object to dispatch

        """
        self.general.broadcast(o)
        with suppress(KeyError):
            channel = self.channels[key]
            channel.broadcast(o)

    def subscribe(self, key: K) -> Subscription[T]:
        """Subscribes to this object.

        Args:
            key (K): key to subscribe to

        Returns:
            Subscription[T]: A subscription object

        """
        channel = self.channels.get(key)
        if channel is None:
            channel = Channel()
            self.channels[key] = channel

        return channel.subscribe()

    def subscribe_all(self) -> Subscription[T]:
        """Subscribes to general channel.

        Returns:
            Subscription[T]: A subscription object

        """
        channel = self.general
        subscription = channel.subscribe()
        return subscription

    def broadcast(self, o: T) -> None:
        """Broadcast an object.

        Args:
            o (T): object to broadcast

        """
        for channel in self.channels.values():
            channel.broadcast(o)
        self.general.broadcast(o)

    def close_channel(self, key: K) -> None:
        """Close one channel.

        Does not raise exception if channel does not exist.

        Args:
            key (K): key of channel to close.

        """
        try:
            channel = self.channels[key]
            channel.close()
            del self.channels[key]
        except KeyError:
            pass

    def close(self) -> None:
        """Close the channel and all subscriptions."""
        for channel in self.channels.values():
            channel.close()
        self.channels = {}
        self.general.close()

    def is_empty(self) -> bool:
        """Returns True if channel has no subscriptions."""
        return (
            all(c.is_empty() for c in self.channels.values())
            and self.general.is_empty()
        )
