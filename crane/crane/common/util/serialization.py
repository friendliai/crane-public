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

"""Custom Serialization utilities."""

from __future__ import annotations

import abc
import json
import pickle
from typing import Dict, List, TypeVar, Union, cast

from google.protobuf.struct_pb2 import Struct
from mashumaro import DataClassJSONMixin, DataClassMessagePackMixin, DataClassYAMLMixin
from mashumaro.types import SerializableType
from typing_extensions import Protocol

from crane.common.util.config import struct_to_dict

P = TypeVar("P", bound="PickleSerializeMixin")
D = TypeVar("D", bound="DictMarshalable")
M = TypeVar("M", bound="DataClassMessagePackMixin")
C = TypeVar("C", bound="CustomSerializeMixin")
S = TypeVar("S", bound="DataClassJSONSerializeMixin")

_JsonValue = Union[str, int, float]
JsonValue = Union[_JsonValue, List[_JsonValue], Dict[str, _JsonValue]]


class PickleSerializeMixin:
    """Python object to bytes."""

    def serialize(self: P) -> bytes:
        """Serialize into bytes.

        Returns:
            bytes: serialized object

        """
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls: type[P], data: bytes) -> P:
        """Deserialize object.

        Args:
            cls (type[P]): class
            data (bytes): serialized data.

        Returns:
            P: original object

        """
        return pickle.loads(data)


class DictMarshalable(Protocol):
    """A protocol that denotes that this class can be mashalled into a dict."""

    def to_dict(self: D) -> str:
        """Marshal into a dictionary."""

    @classmethod
    def from_dict(cls: type[D], data: dict) -> D:
        """Create object from a dictionary."""


class _DictToByteSerializationMixin:
    def serialize(self: D) -> bytes:
        """Serialize."""
        return json.dumps(self.to_dict(), separators=(",", ":")).encode("utf-8")

    @classmethod
    def deserialize(cls: type[D], data: bytes) -> D:
        """Turn bytes into dataclass."""
        return cls.from_dict(json.loads(data.decode("utf-8")))


class DataClassJSONSerializeMixin(_DictToByteSerializationMixin, DataClassJSONMixin):
    """ERM serialization mixin class for dataclasses."""

    # TODO: remove to_struct, from_struct methods
    # implemented here for smooth transition between
    #   DataClassStructMixin and DataClassJSONSerializeMixin
    def to_struct(self: S) -> Struct:
        """Turn dataclass into struct.

        Returns:
            Struct: protobuf struct.

        """
        s = Struct()
        s.update(self.to_dict())
        return s

    @classmethod
    def from_struct(cls: type[S], data: Struct) -> S:
        """Turn struct into dataclass.

        Args:
            cls (type[S]): dataclass
            data (Struct): protobuf struct.

        Returns:
            S: dataclass

        """
        return cls.from_dict(struct_to_dict(data))


class DataClassMsgpackSerializeMixin(DataClassMessagePackMixin):
    """A serialization mixin that serializes into a msgpack."""

    def serialize(self) -> bytes:
        """Serialize."""
        return cast(bytes, self.to_msgpack())

    @classmethod
    def deserialize(cls: type[M], data: bytes) -> M:
        """Turn bytes into dataclass."""
        return cls.from_msgpack(data)


class CustomSerializeMixin(abc.ABC, SerializableType, _DictToByteSerializationMixin):
    """Custom serialization mixin that works both for erm and mashumaro."""

    @abc.abstractmethod
    def _serialize(self) -> dict[str, JsonValue]:
        """Serialize into a dict."""

    @classmethod
    @abc.abstractmethod
    def _deserialize(cls: type[C], value: dict[str, JsonValue]) -> C:
        """Create object from dict."""

    # pylint: disable=unused-argument
    def to_dict(self, *args, **kwargs) -> dict[str, JsonValue]:
        """Serialize into a dict."""
        return self._serialize()

    # pylint: disable=unused-argument
    @classmethod
    def from_dict(cls: type[C], value: dict[str, JsonValue], *args, **kwargs) -> C:
        """Create object from dict."""
        return cls._deserialize(value)

    # pylint: disable=unused-argument
    def to_json(self, *args, **kwargs) -> str:
        """Serialize."""
        return json.dumps(self.to_dict(), separators=(",", ":"))

    # pylint: disable=unused-argument
    @classmethod
    def from_json(cls: type[C], data: str, *args, **kwargs) -> C:
        """Turn bytes into dataclass."""
        return cls.from_dict(json.loads(data))


__all__ = ["DataClassYAMLMixin"]
