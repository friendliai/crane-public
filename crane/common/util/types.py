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

"""Utilities for types and type annotations."""

from __future__ import annotations

import inspect
import sys
from types import MappingProxyType
from typing import Any, Callable, Mapping


def get_global_namespace(cls: type | Callable) -> dict[str, Any]:
    """Get global namespace of class.

    Add itself to globals incase defined in local context
    copy module to resolve issue pydantic/#1228

    """
    ns = sys.modules[cls.__module__].__dict__.copy()
    ns.setdefault(cls.__name__, cls)
    return ns


def get_local_namespace_of_caller() -> Mapping[str, Any]:
    """Get locals.

    dark magic :)

    """
    frame = inspect.currentframe()
    assert frame and frame.f_back and frame.f_back.f_back
    try:
        ns = frame.f_back.f_back.f_locals
        return MappingProxyType(ns)
    finally:
        del frame
