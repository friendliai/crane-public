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

"""Crane user client types."""

from __future__ import annotations

from typing import Optional

import crane.common.constant as C
from crane.lib.aio.client import ClientConfig


class UserLibConfig(ClientConfig):
    """Configuration for crane user client."""

    url: str = f"uds://{C.Gateway.SOCKET.DISTRIBUTED}"
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

    class Meta:
        """Prefix."""

        prefix = "CRANE_USER"
