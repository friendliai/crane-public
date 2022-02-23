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

"""Waiter utility.

Client waits for an event to finish.
Server mark events as finished based on tag
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Awaitable, DefaultDict, Generic, TypeVar

T = TypeVar("T")


class Waiter(Generic[T]):
    """Waiter event class."""

    def __init__(self) -> None:
        """Initialize."""
        self._tickets: DefaultDict[T, list[asyncio.Event]] = defaultdict(list)

    def new(self, tag: T) -> Awaitable[bool]:
        """Create waiting ticket."""
        event = asyncio.Event()
        self._tickets[tag].append(event)
        waiter = event.wait()
        return waiter

    def done(self, tag: T) -> None:
        """Mark events as done."""
        event_list = self._tickets.pop(tag, [])
        for event in event_list:
            event.set()
