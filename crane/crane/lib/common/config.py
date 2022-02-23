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

"""File-backed configuration.

A Configuration object

Similar projects:
    - OmegaConf: parses yaml/json/command line, and returns a Configuration object
        |- Differences: Cannot modify original file.

"""

from __future__ import annotations

import json
import os
from collections import ChainMap
from typing import Any, Mapping, TypeVar, Union, get_type_hints

from crane.common.util.context import atomic_write
from crane.common.util.types import get_global_namespace

T = TypeVar("T", bound="FileBackedConfig")


class FileBackedConfig:
    """Save/load configuration to/from persistent json file."""

    @classmethod
    def load(cls: type[T], file_path: str) -> T:
        """Load configuration from file."""
        return cls(file_path)

    def __init_subclass__(cls) -> None:
        """Subclass hook."""
        globalns = get_global_namespace(cls)
        annotations = get_type_hints(cls, globalns=globalns)

        defaults = {}
        for attr_name, type_annotation in annotations.items():
            if not hasattr(cls, attr_name):
                raise TypeError(
                    f"Configuration has missing default value for {attr_name}"
                )
            default = getattr(cls, attr_name)
            defaults[attr_name] = default

            attr_property = create_property(attr_name, default, type_annotation)

            setattr(cls, attr_name, attr_property)

        setattr(cls, "_defaults", defaults)

    def __init__(self, file_path: str) -> None:
        """Initialize."""
        self._file_path = file_path
        self._config: dict[str, Any] = {}
        self._env_overrides = {}

        self._load_from_file()

        # read from os env
        meta = getattr(self, "Meta", type("Meta", (), {}))
        env_prefix = getattr(meta, "prefix", "")

        globalns = get_global_namespace(self.__class__)
        annotations = get_type_hints(self.__class__, globalns=globalns)

        for attr_name, type_annotation in annotations.items():
            env = f"{env_prefix}_{attr_name}".upper()

            if env in os.environ:
                raw_value = os.environ[env]
                value = parse_value(type_annotation, raw_value)
                self._env_overrides[attr_name] = value

    def save(self) -> None:
        """Save configuration.

        Atomic write via write & rename.
        """
        with atomic_write(self._file_path) as f:
            json.dump(self._config, f)

    def to_dict(self) -> Mapping[str, Any]:
        """Return original configuration dictionary."""
        defaults = getattr(self, "_defaults")
        return dict(ChainMap(self._env_overrides, self._config, defaults))

    def __eq__(self, other: object) -> bool:
        """Return true if two configuration objects are equal."""
        if not isinstance(other, FileBackedConfig):
            return NotImplemented

        return self.to_dict() == other.to_dict()

    def __str__(self) -> str:
        """Return string representation."""
        return str(self.to_dict())

    __repr__ = __str__

    def _load_from_file(self) -> None:
        """Load configuration json from file."""
        if not os.path.exists(self._file_path):
            config_dir = os.path.dirname(self._file_path)
            os.makedirs(config_dir, exist_ok=True)
            self.save()
            return

        with open(self._file_path, "r", encoding="utf8") as f:
            self._config = json.load(f)


# pylint: disable=protected-access
def create_property(attr: str, default: Any, type_annotation: type) -> property:
    """Return a property descriptor given config attribute."""

    def fget(self) -> Any:
        if attr in self._env_overrides:
            return self._env_overrides[attr]
        if attr in self._config:
            return self._config[attr]
        return self._defaults[attr]

    def fset(self, value: Any) -> None:
        self._config[attr] = value

    def fdel(self) -> None:
        self._config[attr] = default

    doc = f"Configuration {attr}[{type_annotation}]"
    return property(fget, fset, fdel, doc)


def parse_value(type_: object, raw_value: str) -> Any:
    """Given stringified value, convert into python object."""
    if isinstance(type_, type):
        return type_(raw_value)

    if not hasattr(type_, "__origin__"):
        raise TypeError(type_)

    origin = getattr(type_, "__origin__")
    args = getattr(type_, "__args__")

    if origin is not Union:
        raise NameError(type_)

    # Optional[~]
    # Union optimizes types so length 0~1 is impossible
    if len(args) != 2 or args[-1] is not type(None):  # noqa: E721
        raise NameError(type_)

    if raw_value == "null":
        return None

    return args[0](raw_value)
