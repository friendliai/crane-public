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

"""Utilities for storing objects."""

from __future__ import annotations

from typing import Generic, Iterator, TypeVar

from crane.common.exception import AlreadyExistError, DoesNotExistError

K = TypeVar("K")
V = TypeVar("V")


class Store(Generic[K, V]):
    """A key-value store.

    Raises if a duplicate key is encountered
    Dictarionay-like class that implement get, add, delete

    Args:
        key_attr (str): assumes key can be received via this attribute

    """

    def __init__(self, key_attr: str):
        """Initialize Store."""
        self._key_attr = key_attr
        self._store: dict[K, V] = {}

    def has(self, key: K) -> bool:
        """Return True if store has model with key.

        Args:
            key (K): key of model

        Returns:
            bool: if key in store

        """
        return key in self._store

    def get(self, key: K) -> V:
        """Get item from store.

        Args:
            key (K): key of the item

        Raises:
            DoesNotExistError: If item does not exist

        Returns:
            V: Item

        """
        if key not in self._store:
            raise DoesNotExistError(key)
        return self._store[key]

    def add(self, item: V):
        """Add a new item to store.

        Args:
            key (K): key of the item
            item (V): Item to add

        Raises:
            AlreadyExistError: If item already exists.
            AttributeError: If key attribute does not exist

        """
        key = getattr(item, self._key_attr)
        if key in self._store:
            raise AlreadyExistError(key)
        self._store[key] = item

    def delete(self, key: K):
        """Delete item from store.

        Args:
            key (K): key of the item

        Raises:
            DoesNotExistError: If item does not exist.

        """
        if key not in self._store:
            raise DoesNotExistError(key)
        del self._store[key]

    def pop(self, key: K) -> V:
        """Pop item from store.

        Args:
            key (K): Id of the model

        Raises:
            DoesNotExistError: If item does not exist

        Returns:
            V: Model that was deleted

        """
        item: V | None = self._store.pop(key, None)
        if item is None:
            raise DoesNotExistError(key)
        return item

    def clear(self) -> None:
        """Reset."""
        self._store = {}

    def __len__(self) -> int:
        """Return number of items."""
        return len(self._store)

    def __contains__(self, key: K) -> bool:
        """Same with has."""
        return self.has(key)

    def __bool__(self) -> bool:
        """True if store is empty."""
        return bool(self._store)

    def __iter__(self) -> Iterator[V]:
        """Return an iterator over all items in the store.

        Returns:
            Iterator[V]: Iterator over items

        """
        return iter(self._store.values())
