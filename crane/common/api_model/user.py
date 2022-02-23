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

"""User."""

from dataclasses import field
from secrets import compare_digest

from crane.common.model import dataclass
from crane.common.util.serialization import DataClassJSONMixin


@dataclass(eq=False)
class Credential(DataClassJSONMixin):
    """User credential."""

    username: str
    password: str = field(repr=False)

    def __eq__(self, other: object) -> bool:
        """Test equality."""
        if not isinstance(other, Credential):
            return NotImplemented

        return self.username == other.username and compare_digest(
            self.password, other.password
        )


@dataclass
class UserInfo(DataClassJSONMixin):
    """User information."""

    id: str
    username: str
    is_superuser: bool


@dataclass
class DeviceFlowInfo(DataClassJSONMixin):
    """Device flow information."""

    redirect_uri: str
    device_code: str


@dataclass
class TokenRequest(DataClassJSONMixin):
    """Access token request payload."""

    device_code: str


@dataclass
class Token(DataClassJSONMixin):
    """User token."""

    access_token: str
    refresh_token: str
