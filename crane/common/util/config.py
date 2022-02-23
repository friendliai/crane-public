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

"""Implement Config class."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple, TypeVar, Union

from google.protobuf.struct_pb2 import ListValue, Struct

JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


def _parse_key_string(key: str) -> list[str]:
    if not key:
        raise KeyError(key)
    key_list = key.split(".")
    return list(key_list)


def _is_subset(sub_dict: dict, super_dict: dict) -> bool:
    for k, v in sub_dict.items():
        if k not in super_dict:
            return False
        o_v = super_dict[k]
        if isinstance(v, dict):
            if not _is_subset(v, o_v):
                return False
        else:
            if v != o_v:
                return False
    return True


def struct_to_dict(s: Struct) -> dict:
    """Transform protobuf struct to python dict (nested).

    Args:
        s (Struct): protobuf data

    Returns:
        dict : transformed dict

    """
    # todo: comment due to disagreement in black and pydocstyle

    def _parse(o):
        if isinstance(o, Struct):
            return struct_to_dict(o)
        if isinstance(o, ListValue):
            return [_parse(i) for i in o]  # type: ignore
        return o

    return {k: _parse(v) for k, v in s.items()}


class ConfigInvalidException(Exception):
    """Raised when a configuration is invalid.

    Args:
        cls (type[Config]): Configuration class (type)
        param (str): name of Parameter that is invalid
        msg (str): reason for invalid configuration

    """

    def __init__(self, cls: type[Config], param: str, msg: str):
        """Initialize."""
        err_str = f"{cls.__name__}.{param}: {msg}"
        super().__init__(err_str)


class _Namespace:
    """Simple object for storing attributes."""

    def __init__(self, **kwargs):
        for name, val in kwargs.items():
            setattr(self, name, val)

    def __eq__(self, other):
        if not isinstance(other, _Namespace):
            raise TypeError
        return vars(self) == vars(other)

    def __contains__(self, key):
        return key in self.__dict__


def _to_namespace(d: dict) -> _Namespace:
    def _parse(o):
        if isinstance(o, dict):
            return _to_namespace(o)
        return o

    values = {k: _parse(v) for k, v in d.items()}
    return _Namespace(**values)


T = TypeVar("T", bound="Config")


class Config(dict):
    """Nested dictionary.

    Used for configurations.
    Keys express nested dict, seperated by '.'
    E.g. "first.second.third"
    """

    def query(self, key: str) -> JSONType:
        """Query an value.

        config.query("key")  # config["key"]
        config.query("key.subkey")  # config["key.subkey"]

        Raises:
            KeyError: if key does not exist

        Returns:
            JSONType: a json-like value

        """
        key_list = _parse_key_string(key)
        dest = self
        for k in key_list:
            dest = dest[k]
        if isinstance(dest, dict):
            return Config(**dest)
        return dest

    def add(self, key: str, value: JSONType):
        """Add a value to config.

        Args:
            key (str): config key
            value (JSONType): json-like value

        Raises:
            KeyError: if key already exists

        """
        dest, last_key = self._parse_key(key)
        if last_key in dest:
            raise KeyError
        dest[last_key] = value

    def remove(self, key: str):
        """Remove a subconfig.

        Args:
            key (str): config key

        Raises:
            KeyError: if key does not exist

        """
        dest, last_key = self._parse_key(key)
        if last_key not in dest:
            raise KeyError
        del dest[last_key]

    def append(self, key: str, *value_list):
        """Append values to config."""
        dest, last_key = self._parse_key(key)
        if last_key not in dest:
            dest[last_key] = []
        dest[last_key].extend(value_list)

    def is_subset(self, config: Config) -> bool:
        """Is a subset of self.

        Args:
            config (Config): config to compare

        Returns:
            bool: True if self is subset of config

        """
        return _is_subset(self, config)

    def is_superset(self, config: Config) -> bool:
        """Do opposite of is_subset."""
        return config.is_subset(self)

    def copy(self: T) -> T:
        """Create a deepcopy."""
        return deepcopy(self)

    def build(self) -> _Namespace:
        """Build dictionary into namespace.

        configurations can be accessed via attributes

        Returns:
            _Namespace: namespace for configuration

        """
        return _to_namespace(self)

    def to_protobuf(self) -> Struct:
        """Serialize this config into a protobuf message.

        Returns:
            Struct: Struct message

        """
        s = Struct()
        s.update(self)
        return s

    @classmethod
    def from_protobuf(cls, s: Struct):
        """Deserialize from a protobuf message.

        Returns:
            Config: dict-like object

        """
        d = struct_to_dict(s)
        return cls(**d)

    def _parse_key(self, key: str) -> Tuple[dict, str]:
        key_list = _parse_key_string(key)
        last_key = key_list[-1]
        key_list = key_list[:-1]

        dest = self
        for k in key_list:
            if k not in dest:
                dest[k] = {}
            dest = dest[k]
            if not isinstance(dest, dict):
                raise KeyError

        return dest, last_key
