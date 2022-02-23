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

"""Workspace Model."""

from __future__ import annotations

from crane.common.model import dataclass
from crane.common.util.serialization import DataClassJSONSerializeMixin


@dataclass(frozen=True)
class BaseWorkspace(DataClassJSONSerializeMixin):
    """Base workspace constructs.

    Args:
        id (str): Workspace id
        container_path (str): Container path where tarball should be copied into
        tarball_path (str): Path where pulled tarball is placed

    """

    id: str  # pylint: disable=invalid-name
    container_path: str
    tarball_path: str


@dataclass(frozen=True)
class LocalWorkspace(BaseWorkspace):
    """Workspace that has local tarball path."""


@dataclass(frozen=True)
class RemoteWorkspace(BaseWorkspace):
    """Workspace that has remote tarball path."""


@dataclass(frozen=True)
class WorkspaceEnvVar(DataClassJSONSerializeMixin):
    """Environment variable configured from user workspace.

    Args:
        key (str): Environment variable key
        value (str): Environment variable value

    """

    key: str
    value: str
