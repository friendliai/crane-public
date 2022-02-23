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


"""Implement context manager helpers."""

import os
from contextlib import asynccontextmanager, contextmanager
from secrets import token_hex
from typing import IO, Any, AsyncIterator, Iterator, TypeVar

import aiofiles
import aiofiles.os
from aiofiles.threadpool import AsyncTextIOWrapper  # type: ignore
from typing_extensions import Protocol


class SupportsAsyncClose(Protocol):
    """A protocol that defines async close method."""

    async def close(self) -> None:
        """Close context."""


T = TypeVar("T", bound=SupportsAsyncClose)


class AsyncClosingContextManagerMixin:
    """Mixin class for async context manager that closes at exit."""

    async def __aenter__(self: T) -> T:
        """Enter context manager."""
        return self

    async def __aexit__(self: T, *_: Any) -> None:
        """Close object and exit context manager."""
        await self.close()


@asynccontextmanager
async def aclosing(obj: T) -> AsyncIterator[T]:
    """Async version of contextlib.closing.

    Note) MYPY can't resolve typevars in asynccontextmanager
          https://github.com/python/mypy/issues/9922

    """
    try:
        yield obj
    finally:
        await obj.close()


@contextmanager
def atomic_write(path: str) -> Iterator[IO]:
    """Returns a file handle that atomically write to the given path.

    Args:
        path (str): Path to which the atomic write should be performed.

    """
    temp_path = f"{path}.{token_hex(10)}"

    with open(temp_path, "w", encoding="utf8") as f:
        yield f

    os.rename(temp_path, path)


@asynccontextmanager
async def async_atomic_write(path: str) -> AsyncIterator[AsyncTextIOWrapper]:
    """Returns an aiofile handle that atomically writes to the given path.

    Args:
        path (str): Path to which the atomic write should be performed.

    """
    temp_path = f"{path}.{token_hex(10)}"

    async with aiofiles.open(temp_path, "w") as f:
        yield f

    await aiofiles.os.rename(temp_path, path)
